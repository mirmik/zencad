"""Fluent typed wire authoring over immutable expression handles."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast, overload

from ._core import require_same_runtime
from .runtime import Runtime
from .topology import Edge, Wire
from .values import Point3, ScalarInput, Vector3


PointInput = Point3 | Vector3 | Sequence[ScalarInput]
VectorInput = Point3 | Vector3 | Sequence[ScalarInput]


class WireBuilder:
    """A mutable cursor that only assembles immutable typed graph handles."""

    def __init__(
        self,
        start: PointInput = (0, 0, 0),
        defrel: bool = False,
        *,
        runtime: Runtime | None = None,
    ) -> None:
        if runtime is None:
            if not isinstance(start, (Point3, Vector3)):
                raise TypeError("literal WireBuilder start requires runtime=")
            runtime = start.runtime
        if not isinstance(runtime, Runtime):
            raise TypeError("WireBuilder runtime must be Runtime")
        if not isinstance(defrel, bool):
            raise TypeError("WireBuilder defrel must be bool")
        self.runtime = runtime
        self.edges: list[Edge] = []
        self.current = self._point(start)
        self.start = self.current
        self.default_rel = defrel
        self._at_start = True

    def _point(self, value: PointInput) -> Point3:
        if isinstance(value, Point3):
            require_same_runtime(self.runtime, value)
        elif isinstance(value, Vector3):
            require_same_runtime(self.runtime, value)
        return self.runtime.point3(value)

    def _vector(self, value: VectorInput) -> Vector3:
        if isinstance(value, Point3):
            require_same_runtime(self.runtime, value)
        elif isinstance(value, Vector3):
            require_same_runtime(self.runtime, value)
        return self.runtime.vector3(value)

    @staticmethod
    def collect_point(
        pnt: ScalarInput | PointInput,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
    ) -> ScalarInput | PointInput:
        if z is not None:
            if y is None:
                raise TypeError("z coordinate requires y coordinate")
            return (cast(ScalarInput, pnt), y, z)
        if y is not None:
            return (cast(ScalarInput, pnt), y)
        return pnt

    def prepare(
        self,
        pnts: Sequence[PointInput],
        rel: bool | None = None,
    ) -> list[Point3]:
        relative = self.default_rel if rel is None else rel
        if not isinstance(relative, bool):
            raise TypeError("WireBuilder rel must be bool or None")
        if relative:
            return [self.current + self._vector(point) for point in pnts]
        return [self._point(point) for point in pnts]

    @overload
    def restart(self, pnt: PointInput) -> WireBuilder: ...

    @overload
    def restart(
        self,
        pnt: ScalarInput,
        y: ScalarInput,
        z: ScalarInput | None = None,
    ) -> WireBuilder: ...

    def restart(
        self,
        pnt: ScalarInput | PointInput,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
    ) -> WireBuilder:
        value = self.collect_point(pnt, y, z)
        self.edges = []
        self.current = self._point(cast(PointInput, value))
        self.start = self.current
        self._at_start = True
        return self

    @overload
    def segment(
        self,
        pnt: PointInput,
        *,
        rel: bool | None = None,
    ) -> WireBuilder: ...

    @overload
    def segment(
        self,
        pnt: ScalarInput,
        y: ScalarInput,
        z: ScalarInput | None = None,
        rel: bool | None = None,
    ) -> WireBuilder: ...

    def segment(
        self,
        pnt: ScalarInput | PointInput,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        rel: bool | None = None,
    ) -> WireBuilder:
        value = self.collect_point(pnt, y, z)
        target = self.prepare((cast(PointInput, value),), rel)[0]
        self.edges.append(self.runtime.segment(self.current, target))
        self.current = target
        self._at_start = target is self.start
        return self

    line = segment
    l = segment  # noqa: E741

    def arc_by_points(
        self,
        a: PointInput,
        b: PointInput,
        rel: bool | None = None,
    ) -> WireBuilder:
        middle, target = self.prepare((a, b), rel)
        self.edges.append(self.runtime.circle_arc(self.current, middle, target))
        self.current = target
        self._at_start = target is self.start
        return self

    def arc(
        self,
        center: PointInput,
        radius: ScalarInput,
        angle: ScalarInput,
        rel: bool | None = None,
    ) -> WireBuilder:
        resolved_center = self.prepare((center,), rel)[0]
        curve = self.runtime.circle(radius).transform(
            self.runtime.translation(resolved_center.to_vector3())
        )
        first = curve.lower_distance_parameter(self.current)
        last = first + angle
        self.edges.append(curve.edge((first, last)))
        self.current = curve.point(last)
        self._at_start = False
        return self

    def elliptic_arc(
        self,
        center: PointInput,
        radius1: ScalarInput,
        radius2: ScalarInput,
        angle: ScalarInput,
        rotate: ScalarInput = 0,
        rel: bool | None = None,
    ) -> WireBuilder:
        resolved_center = self.prepare((center,), rel)[0]
        curve = (
            self.runtime.ellipse(radius1, radius2)
            .transform(self.runtime.rotateZ(rotate))
            .transform(self.runtime.translation(resolved_center.to_vector3()))
        )
        first = curve.lower_distance_parameter(self.current)
        last = first + angle
        self.edges.append(curve.edge((first, last)))
        self.current = curve.point(last)
        self._at_start = False
        return self

    def interpolate(
        self,
        pnts: Sequence[PointInput],
        tangs: Sequence[VectorInput | None] | None = None,
        curtang: VectorInput = (0, 0, 0),
        approx: bool = False,
        rel: bool | None = None,
    ) -> WireBuilder:
        if not isinstance(approx, bool):
            raise TypeError("WireBuilder interpolate approx must be bool")
        points = self.prepare(pnts, rel)
        if not points:
            raise ValueError("WireBuilder interpolate requires at least one point")
        if tangs is None:
            resolved_tangents: list[Vector3 | None] = [
                self.runtime.vector3() for _ in points
            ]
        else:
            if len(tangs) != len(points):
                raise ValueError("WireBuilder tangents must match point count")
            resolved_tangents = [
                None if tangent is None else self._vector(tangent)
                for tangent in tangs
            ]
        if approx:
            if not self.edges:
                raise ValueError("WireBuilder approximate interpolation needs an edge")
            current_tangent = self.edges[-1].d1(self.edges[-1].range().upper)
        else:
            current_tangent = self._vector(curtang)
        self.edges.append(
            self.runtime.interpolate(
                (self.current, *points),
                (current_tangent, *resolved_tangents),
            )
        )
        self.current = points[-1]
        self._at_start = self.current is self.start
        return self

    def close(self, approx_a: bool = False, approx_b: bool = False) -> WireBuilder:
        if not isinstance(approx_a, bool) or not isinstance(approx_b, bool):
            raise TypeError("WireBuilder close approximation flags must be bool")
        if self._at_start:
            return self
        if not self.edges:
            raise ValueError("WireBuilder cannot close without edges")
        if not approx_a and not approx_b:
            self.edges.append(self.runtime.segment(self.current, self.start))
        else:
            tangent_a = (
                self.edges[-1].d1(self.edges[-1].range().upper)
                if approx_a
                else self.runtime.vector3()
            )
            tangent_b = (
                self.edges[0].d1(self.edges[0].range().lower)
                if approx_b
                else self.runtime.vector3()
            )
            self.edges.append(
                self.runtime.interpolate(
                    (self.current, self.start),
                    (tangent_a, tangent_b),
                )
            )
        self.current = self.start
        self._at_start = True
        return self

    def svg_elliptic_arc(
        self,
        radius_x: ScalarInput,
        radius_y: ScalarInput,
        x_axis_angle: ScalarInput,
        large: bool,
        sweep: bool,
        x: ScalarInput,
        y: ScalarInput,
    ) -> WireBuilder:
        target = self.runtime.point3(x, y, 0)
        self.edges.append(
            self.runtime._svg_elliptic_arc(
                self.current,
                target,
                radius_x,
                radius_y,
                x_axis_angle,
                large,
                sweep,
            )
        )
        self.current = target
        self._at_start = target is self.start
        return self

    def svg_circle_arc(
        self,
        radius: ScalarInput,
        x_axis_angle: ScalarInput,
        large: bool,
        sweep: bool,
        x: ScalarInput,
        y: ScalarInput,
    ) -> WireBuilder:
        return self.svg_elliptic_arc(
            radius,
            radius,
            x_axis_angle,
            large,
            sweep,
            x,
            y,
        )

    def plane_circle_arc(
        self,
        radius: ScalarInput,
        angle: ScalarInput,
        large: bool,
        sweep: bool,
        x: ScalarInput,
        y: ScalarInput,
    ) -> WireBuilder:
        del angle
        return self.svg_circle_arc(radius, 0, large, sweep, x, y)

    def build(self) -> Wire:
        if not self.edges:
            raise ValueError("WireBuilder has no edges")
        return self.runtime.make_wire(self.edges)

    def doit(self) -> Wire:
        return self.build()


wire_builder = WireBuilder


__all__ = ["WireBuilder", "wire_builder"]
