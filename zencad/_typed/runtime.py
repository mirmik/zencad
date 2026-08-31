"""Experimental typed ZenCad domain handles.

This module is intentionally private.  It is the vertical slice used to prove
that a stable domain API can contain an evalcache expression graph without
exposing lazy proxy types to callers.
"""

from __future__ import annotations

from collections.abc import Sequence
import math
from os import PathLike
from typing import TYPE_CHECKING, Callable, Literal, TypeVar, cast, overload

from OCP.TopoDS import TopoDS_Vertex
from OCP.Geom import Geom_CartesianPoint
from OCP.gp import gp_Dir, gp_Pnt, gp_Quaternion, gp_Vec, gp_XYZ
from evalcache.v2 import (
    CachePolicy,
    CacheStore,
    EvaluationMode,
    Evaluator,
    Expression,
    MappingCacheStore,
    ProgressHook,
    ResultSpec,
)

from zencad.occ_compat import vertex_point

from . import _operations as ops
from . import _bound_operations as bound_ops
from . import _curve_operations as curve_ops
from . import _surface_operations as surface_ops
from . import _text_operations as text_ops
from . import _transform_operations as transform_ops
from ._core import State, require_same_runtime
from .bounds import BOUNDARY_BOX_SPEC, BoundaryBox
from .curves import CURVE2_SPEC, CURVE_SPEC, Curve, Curve2
from .exttrans import MultiTransform
from .records import Interval
from .surfaces import SURFACE_SPEC, Surface, SweepTrihedron
from .text import FontAspect
from .topology import (
    COMPOUND_SPEC,
    EDGE_SPEC,
    FACE_SPEC,
    SHAPE_SPEC,
    SHELL_SPEC,
    SOLID_SPEC,
    WIRE_SPEC,
    Compound,
    CompSolid,
    DeferredSequence,
    Edge,
    Face,
    Shape,
    Shell,
    Solid,
    Vertex,
    Wire,
)
from .transforms import (
    AFFINE_TRANSFORM_SPEC,
    QUATERNION_SPEC,
    TRANSFORM_SPEC,
    AffineTransform,
    Quaternion,
    Transform,
)
from .values import (
    Number,
    Point2,
    Point3,
    Scalar,
    ScalarInput,
    Vector2,
    Vector3,
    _scalar_state,
)

if TYPE_CHECKING:
    from .wire_builder import WireBuilder


ResolvedT = TypeVar("ResolvedT")

__all__ = [
    "Compound",
    "CompSolid",
    "BoundaryBox",
    "Curve",
    "Curve2",
    "DeferredSequence",
    "Edge",
    "Face",
    "FontAspect",
    "Runtime",
    "Shape",
    "Shell",
    "Solid",
    "Surface",
    "SweepTrihedron",
    "Vertex",
    "Wire",
]


class Runtime:
    """Own one expression evaluator and its independent cache policy."""

    CACHE_NAMESPACE = "zencad-typed-v1"

    def __init__(
        self,
        *,
        mode: EvaluationMode | str = EvaluationMode.DEFERRED,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> None:
        resolved_mode = EvaluationMode(mode)
        if cache:
            policy = CachePolicy(namespace=self.CACHE_NAMESPACE)
            if cache_store is None:
                from zencad.lazifier import lazy

                cache_store = MappingCacheStore(lazy.cache)
        else:
            policy = CachePolicy.disabled(namespace=self.CACHE_NAMESPACE)
            cache_store = None
        self._evaluator = Evaluator(
            mode=resolved_mode,
            cache_policy=policy,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @classmethod
    def deferred(
        cls,
        *,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> Runtime:
        return cls(
            mode=EvaluationMode.DEFERRED,
            cache=cache,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @classmethod
    def immediate(
        cls,
        *,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> Runtime:
        return cls(
            mode=EvaluationMode.IMMEDIATE,
            cache=cache,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @property
    def mode(self) -> EvaluationMode:
        return self._evaluator.mode

    @property
    def cache_enabled(self) -> bool:
        return self._evaluator.cache_policy.enabled

    def _expression(
        self,
        operation: Callable[..., ResolvedT],
        *,
        result: ResultSpec[ResolvedT],
        args: tuple[object, ...],
        operation_id: str,
        cacheable: bool = True,
    ) -> Expression[ResolvedT]:
        expression = self._evaluator.expression(
            operation,
            result=result,
            args=args,
            operation_id=operation_id,
            operation_version="1",
            cacheable=cacheable,
        )
        if self.mode is EvaluationMode.IMMEDIATE:
            self._evaluator.evaluate(expression)
        return expression

    def _resolve(self, expression: Expression[ResolvedT]) -> ResolvedT:
        return self._evaluator.evaluate(expression)

    def _value_state(
        self,
        operation: Callable[..., ResolvedT],
        *,
        result: ResultSpec[ResolvedT],
        args: tuple[object, ...],
        operation_id: str,
    ) -> State[ResolvedT]:
        """Fold resolved value operands; otherwise retain a typed expression."""
        if all(not isinstance(argument, Expression) for argument in args):
            value = operation(*args)
            return result.validate(value, operation_id)
        expression = self._evaluator.expression(
            operation,
            result=result,
            args=args,
            operation_id=operation_id,
            operation_version="1",
        )
        if self.mode is EvaluationMode.IMMEDIATE:
            return self._evaluator.evaluate(expression)
        return expression

    def box(
        self,
        x: ScalarInput | Vector3 | Sequence[ScalarInput] = 0,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        center: bool | str | None = None,
        size: ScalarInput | Vector3 | Sequence[ScalarInput] | None = None,
    ) -> Solid:
        resolved_center = _require_center(center, "box center")
        resolved_size = _box_size(self, x, y, z, size)
        expression = self._expression(
            ops.box,
            result=SOLID_SPEC,
            args=(resolved_size._state, resolved_center),
            operation_id="zencad.typed.box",
        )
        return Solid._from_state(self, expression)

    def cube(
        self,
        x: ScalarInput | Vector3 | Sequence[ScalarInput] = 0,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        center: bool | str | None = None,
        size: ScalarInput | Vector3 | Sequence[ScalarInput] | None = None,
    ) -> Solid:
        """Compatibility alias for :meth:`box` with the legacy signature."""
        return self.box(x, y, z, center, size)

    def sphere(
        self,
        r: ScalarInput,
        yaw: ScalarInput | None = None,
        pitch: ScalarInput | Sequence[ScalarInput] | None = None,
    ) -> Solid:
        expression = self._expression(
            ops.sphere,
            result=SOLID_SPEC,
            args=(
                _scalar_state(self, r),
                _optional_scalar_state(self, yaw),
                _angle_state(self, pitch, "sphere pitch"),
            ),
            operation_id="zencad.typed.sphere",
        )
        return Solid._from_state(self, expression)

    def cylinder(
        self,
        r: ScalarInput,
        h: ScalarInput,
        yaw: ScalarInput | None = None,
        center: bool = False,
    ) -> Solid:
        _require_bool(center, "cylinder center")
        expression = self._expression(
            ops.cylinder,
            result=SOLID_SPEC,
            args=(
                _scalar_state(self, r),
                _scalar_state(self, h),
                _optional_scalar_state(self, yaw),
                center,
            ),
            operation_id="zencad.typed.cylinder",
        )
        return Solid._from_state(self, expression)

    def cone(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        h: ScalarInput,
        yaw: ScalarInput | None = None,
        center: bool = False,
    ) -> Solid:
        _require_bool(center, "cone center")
        expression = self._expression(
            ops.cone,
            result=SOLID_SPEC,
            args=(
                _scalar_state(self, r1),
                _scalar_state(self, r2),
                _scalar_state(self, h),
                _optional_scalar_state(self, yaw),
                center,
            ),
            operation_id="zencad.typed.cone",
        )
        return Solid._from_state(self, expression)

    def torus(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        yaw: ScalarInput | None = None,
        pitch: ScalarInput | Sequence[ScalarInput] | None = None,
    ) -> Solid:
        expression = self._expression(
            ops.torus,
            result=SOLID_SPEC,
            args=(
                _scalar_state(self, r1),
                _scalar_state(self, r2),
                _optional_scalar_state(self, yaw),
                _angle_state(self, pitch, "torus pitch"),
            ),
            operation_id="zencad.typed.torus",
        )
        return Solid._from_state(self, expression)

    def halfspace(self) -> Solid:
        expression = self._expression(
            ops.halfspace,
            result=SOLID_SPEC,
            args=(),
            operation_id="zencad.typed.halfspace",
        )
        return Solid._from_state(self, expression)

    def make_solid(self, shells: Shell | Sequence[Shell], /) -> Solid:
        values = _require_shells(self, shells, "make_solid")
        expression = self._expression(
            ops.make_solid,
            result=SOLID_SPEC,
            args=(tuple(shell._state for shell in values),),
            operation_id="zencad.typed.make_solid",
        )
        return Solid._from_state(self, expression)

    def empty_shape(self) -> Shape:
        """Return the algebraic zero of topology without materializing it."""
        expression = self._expression(
            ops.empty_shape,
            result=SHAPE_SPEC,
            args=(),
            operation_id="zencad.typed.empty_shape",
        )
        return Shape._from_state(self, expression)

    def nullshape(self) -> Shape:
        """Legacy spelling for :meth:`empty_shape`."""
        return self.empty_shape()

    def union(
        self,
        shapes: Shape | Sequence[Shape],
        /,
        *others: Shape,
    ) -> Shape:
        values = _require_shapes(self, shapes, others, "union")
        expression = self._expression(
            ops.union_shapes,
            result=SHAPE_SPEC,
            args=(tuple(shape._state for shape in values),),
            operation_id="zencad.typed.union",
        )
        return Shape._from_state(self, expression)

    def intersect(
        self,
        shapes: Shape | Sequence[Shape],
        /,
        *others: Shape,
    ) -> Shape:
        values = _require_shapes(self, shapes, others, "intersect")
        expression = self._expression(
            ops.intersection_shapes,
            result=SHAPE_SPEC,
            args=(tuple(shape._state for shape in values),),
            operation_id="zencad.typed.intersect",
        )
        return Shape._from_state(self, expression)

    def intersection(
        self,
        shapes: Shape | Sequence[Shape],
        /,
        *others: Shape,
    ) -> Shape:
        """Descriptive alias for the legacy :meth:`intersect` spelling."""
        return self.intersect(shapes, *others)

    def difference(
        self,
        shapes: Shape | Sequence[Shape],
        /,
        *others: Shape,
    ) -> Shape:
        values = _require_shapes(self, shapes, others, "difference")
        expression = self._expression(
            ops.difference_shapes,
            result=SHAPE_SPEC,
            args=(tuple(shape._state for shape in values),),
            operation_id="zencad.typed.difference",
        )
        return Shape._from_state(self, expression)

    def section(
        self,
        left: Shape | ScalarInput | Point3 | Vector3 | Sequence[ScalarInput],
        right: Shape | ScalarInput | Point3 | Vector3 | Sequence[ScalarInput] = 0,
        /,
        *,
        pretty: bool = False,
    ) -> Shape:
        """Intersect shape boundaries, accepting legacy plane operands."""
        _require_bool(pretty, "section pretty")
        left_shape = _section_operand(self, left, "section left")
        right_shape = _section_operand(self, right, "section right")
        expression = self._expression(
            ops.section,
            result=SHAPE_SPEC,
            args=(left_shape._state, right_shape._state, pretty),
            operation_id="zencad.typed.section",
        )
        return Shape._from_state(self, expression)

    def empty_boundary_box(self) -> BoundaryBox:
        """Return the identity value for boundary-box union."""
        return BoundaryBox._from_state(self, bound_ops.empty_boundary_box())

    def boundary_box(self, minimum: Point3, maximum: Point3, /) -> BoundaryBox:
        """Create a graph-preserving box from its opposite corner points."""
        if not isinstance(minimum, Point3) or not isinstance(maximum, Point3):
            raise TypeError("boundary_box expects Point3 corners")
        require_same_runtime(self, minimum)
        require_same_runtime(self, maximum)
        state = self._value_state(
            bound_ops.boundary_box_from_points,
            result=BOUNDARY_BOX_SPEC,
            args=(minimum._state, maximum._state),
            operation_id="zencad.typed.boundary-box.from-points",
        )
        return BoundaryBox._from_state(self, state)

    def line(self, origin: Point3, direction: Vector3, /) -> Curve:
        if not isinstance(origin, Point3):
            raise TypeError("line origin must be Point3")
        if not isinstance(direction, Vector3):
            raise TypeError("line direction must be Vector3")
        require_same_runtime(self, origin)
        require_same_runtime(self, direction)
        expression = self._expression(
            curve_ops.line,
            result=CURVE_SPEC,
            args=(origin._state, direction._state),
            operation_id="zencad.typed.line",
        )
        return Curve._from_state(self, expression)

    def circle_curve(self, radius: ScalarInput, /) -> Curve:
        expression = self._expression(
            curve_ops.circle,
            result=CURVE_SPEC,
            args=(_scalar_state(self, radius),),
            operation_id="zencad.typed.circle_curve",
        )
        return Curve._from_state(self, expression)

    def ellipse_curve(
        self,
        major_radius: ScalarInput,
        minor_radius: ScalarInput,
        /,
    ) -> Curve:
        expression = self._expression(
            curve_ops.ellipse,
            result=CURVE_SPEC,
            args=(
                _scalar_state(self, major_radius),
                _scalar_state(self, minor_radius),
            ),
            operation_id="zencad.typed.ellipse_curve",
        )
        return Curve._from_state(self, expression)

    def interpolate_curve(
        self,
        pnts: Sequence[Point3],
        tangs: Sequence[Vector3 | None] | None = None,
        closed: bool = False,
    ) -> Curve:
        _require_bool(closed, "interpolate_curve closed")
        points = _require_points(self, pnts, minimum=2, name="interpolate_curve")
        tangents = _require_tangents(self, tangs, len(points), "interpolate_curve")
        expression = self._expression(
            curve_ops.interpolate,
            result=CURVE_SPEC,
            args=(
                tuple(point._state for point in points),
                None
                if tangents is None
                else tuple(
                    None if tangent is None else tangent._state for tangent in tangents
                ),
                closed,
            ),
            operation_id="zencad.typed.interpolate_curve",
        )
        return Curve._from_state(self, expression)

    def interpolate(
        self,
        pnts: Sequence[Point3],
        tangs: Sequence[Vector3 | None] | None = None,
        closed: bool = False,
    ) -> Edge:
        return self.interpolate_curve(pnts, tangs, closed).edge()

    def bezier_curve(
        self,
        poles: Sequence[Point3],
        weights: Sequence[ScalarInput] | None = None,
    ) -> Curve:
        points = _require_points(self, poles, minimum=2, name="bezier_curve")
        resolved_weights = _optional_scalar_sequence_state(
            self,
            weights,
            "bezier_curve weights",
        )
        expression = self._expression(
            curve_ops.bezier,
            result=CURVE_SPEC,
            args=(tuple(point._state for point in points), resolved_weights),
            operation_id="zencad.typed.bezier_curve",
        )
        return Curve._from_state(self, expression)

    def bezier(
        self,
        pnts: Sequence[Point3],
        weights: Sequence[ScalarInput] | None = None,
    ) -> Edge:
        return self.bezier_curve(pnts, weights).edge()

    def bspline_curve(
        self,
        poles: Sequence[Point3],
        knots: Sequence[ScalarInput],
        muls: Sequence[int],
        degree: int,
        periodic: bool = False,
        weights: Sequence[ScalarInput] | None = None,
        check_rational: bool | None = None,
    ) -> Curve:
        points = _require_points(self, poles, minimum=2, name="bspline_curve")
        if isinstance(degree, bool) or not isinstance(degree, int) or degree < 1:
            raise ValueError("bspline_curve degree must be a positive int")
        _require_bool(periodic, "bspline_curve periodic")
        if check_rational is not None:
            _require_bool(check_rational, "bspline_curve check_rational")
        knot_states = _scalar_sequence_state(self, knots, "bspline_curve knots")
        multiplicities = _int_sequence(muls, "bspline_curve multiplicities")
        if len(knot_states) != len(multiplicities):
            raise ValueError(
                "bspline_curve knots and multiplicities must have equal length"
            )
        resolved_weights = _optional_scalar_sequence_state(
            self,
            weights,
            "bspline_curve weights",
        )
        expression = self._expression(
            curve_ops.bspline,
            result=CURVE_SPEC,
            args=(
                tuple(point._state for point in points),
                knot_states,
                multiplicities,
                degree,
                periodic,
                resolved_weights,
                check_rational,
            ),
            operation_id="zencad.typed.bspline_curve",
        )
        return Curve._from_state(self, expression)

    def bspline(
        self,
        poles: Sequence[Point3],
        knots: Sequence[ScalarInput],
        muls: Sequence[int],
        degree: int,
        periodic: bool = False,
        weights: Sequence[ScalarInput] | None = None,
        check_rational: bool | None = None,
    ) -> Edge:
        return self.bspline_curve(
            poles,
            knots,
            muls,
            degree,
            periodic,
            weights,
            check_rational,
        ).edge()

    def make_edge(
        self,
        curve: Curve,
        interval: Interval | Sequence[ScalarInput] | None = None,
        /,
    ) -> Edge:
        if not isinstance(curve, Curve):
            raise TypeError("make_edge expects Curve")
        require_same_runtime(self, curve)
        resolved_interval = _interval_state(self, interval, "make_edge interval")
        expression = self._expression(
            ops.curve_edge,
            result=EDGE_SPEC,
            args=(curve._state, resolved_interval),
            operation_id="zencad.typed.make_edge",
        )
        return Edge._from_state(self, expression)

    def circle_arc(self, p1: Point3, p2: Point3, p3: Point3, /) -> Edge:
        points = _require_points(self, (p1, p2, p3), minimum=3, name="circle_arc")
        expression = self._expression(
            ops.circle_arc,
            result=EDGE_SPEC,
            args=tuple(point._state for point in points),
            operation_id="zencad.typed.circle_arc",
        )
        return Edge._from_state(self, expression)

    def _svg_elliptic_arc(
        self,
        start: Point3,
        end: Point3,
        radius_x: ScalarInput,
        radius_y: ScalarInput,
        x_axis_angle: ScalarInput,
        large: bool,
        sweep: bool,
    ) -> Edge:
        _require_points(self, (start, end), minimum=2, name="SVG arc")
        _require_bool(large, "SVG arc large")
        _require_bool(sweep, "SVG arc sweep")
        expression = self._expression(
            ops.svg_elliptic_arc,
            result=EDGE_SPEC,
            args=(
                start._state,
                end._state,
                _scalar_state(self, radius_x),
                _scalar_state(self, radius_y),
                _scalar_state(self, x_axis_angle),
                large,
                sweep,
            ),
            operation_id="zencad.typed.svg_elliptic_arc",
        )
        return Edge._from_state(self, expression)

    def make_wire(
        self,
        *shapes: Edge | Wire | Sequence[Edge | Wire],
    ) -> Wire:
        values = _require_wire_parts(self, shapes, "make_wire")
        expression = self._expression(
            ops.make_wire,
            result=WIRE_SPEC,
            args=(tuple(shape._state for shape in values),),
            operation_id="zencad.typed.make_wire",
        )
        return Wire._from_state(self, expression)

    def wire_builder(
        self,
        start: Point3 | Vector3 | Sequence[ScalarInput] = (0, 0, 0),
        defrel: bool = False,
    ) -> WireBuilder:
        """Create a fluent authoring cursor over immutable typed graph nodes."""
        from .wire_builder import WireBuilder

        return WireBuilder(start=start, defrel=defrel, runtime=self)

    def rounded_polysegment(
        self,
        pnts: Sequence[Point3],
        r: ScalarInput,
        closed: bool = False,
    ) -> Wire:
        _require_bool(closed, "rounded_polysegment closed")
        points = _require_points(self, pnts, minimum=2, name="rounded_polysegment")
        expression = self._expression(
            ops.rounded_polysegment,
            result=WIRE_SPEC,
            args=(
                tuple(point._state for point in points),
                _scalar_state(self, r),
                closed,
            ),
            operation_id="zencad.typed.rounded_polysegment",
        )
        return Wire._from_state(self, expression)

    def helix(
        self,
        r: ScalarInput,
        h: ScalarInput,
        step: ScalarInput | None = None,
        pitch: ScalarInput | None = None,
        angle: ScalarInput = 0,
        left: bool = False,
    ) -> Wire:
        if step is None and pitch is None:
            raise TypeError("helix requires step or pitch")
        _require_bool(left, "helix left")
        expression = self._expression(
            ops.helix,
            result=WIRE_SPEC,
            args=(
                _scalar_state(self, r),
                _scalar_state(self, h),
                _optional_scalar_state(self, step),
                _optional_scalar_state(self, pitch),
                _scalar_state(self, angle),
                left,
            ),
            operation_id="zencad.typed.helix",
        )
        return Wire._from_state(self, expression)

    def segment2(self, start: Point2, end: Point2, /) -> Curve2:
        if not isinstance(start, Point2) or not isinstance(end, Point2):
            raise TypeError("segment2 expects Point2 endpoints")
        require_same_runtime(self, start)
        require_same_runtime(self, end)
        expression = self._expression(
            curve_ops.segment2,
            result=CURVE2_SPEC,
            args=(start._state, end._state),
            operation_id="zencad.typed.segment2",
        )
        return Curve2._from_state(self, expression)

    def ellipse2(
        self,
        major_radius: ScalarInput,
        minor_radius: ScalarInput,
        /,
    ) -> Curve2:
        expression = self._expression(
            curve_ops.ellipse2,
            result=CURVE2_SPEC,
            args=(
                _scalar_state(self, major_radius),
                _scalar_state(self, minor_radius),
            ),
            operation_id="zencad.typed.ellipse2",
        )
        return Curve2._from_state(self, expression)

    def trim_curve2(
        self,
        curve: Curve2,
        start: ScalarInput,
        end: ScalarInput,
        /,
    ) -> Curve2:
        if not isinstance(curve, Curve2):
            raise TypeError("trim_curve2 expects Curve2")
        require_same_runtime(self, curve)
        expression = self._expression(
            curve_ops.trim_curve2,
            result=CURVE2_SPEC,
            args=(
                curve._state,
                _scalar_state(self, start),
                _scalar_state(self, end),
            ),
            operation_id="zencad.typed.trim_curve2",
        )
        return Curve2._from_state(self, expression)

    def cylinder_surface(self, radius: ScalarInput, /) -> Surface:
        expression = self._expression(
            surface_ops.cylinder_surface,
            result=SURFACE_SPEC,
            args=(_scalar_state(self, radius),),
            operation_id="zencad.typed.cylinder_surface",
        )
        return Surface._from_state(self, expression)

    def sweep_surface(
        self,
        section: Curve,
        spine: Curve,
        /,
        *,
        scale: ScalarInput = 1,
        trihedron: SweepTrihedron = SweepTrihedron.CORRECTED_FRENET,
        tolerance: Number = 1e-6,
        continuity: int = 2,
        max_degree: int = 5,
        max_segments: int = 20,
    ) -> Surface:
        if not isinstance(section, Curve):
            raise TypeError("sweep_surface section must be Curve")
        if not isinstance(spine, Curve):
            raise TypeError("sweep_surface spine must be Curve")
        require_same_runtime(self, section)
        require_same_runtime(self, spine)
        if not isinstance(trihedron, SweepTrihedron):
            raise TypeError("sweep_surface trihedron must be SweepTrihedron")
        resolved_tolerance = _require_positive_number(
            tolerance,
            "sweep_surface tolerance",
        )
        resolved_continuity = _require_int_between(
            continuity,
            "sweep_surface continuity",
            minimum=0,
            maximum=3,
        )
        resolved_max_degree = _require_positive_int(
            max_degree,
            "sweep_surface max_degree",
        )
        resolved_max_segments = _require_positive_int(
            max_segments,
            "sweep_surface max_segments",
        )
        expression = self._expression(
            surface_ops.sweep_surface,
            result=SURFACE_SPEC,
            args=(
                section._state,
                spine._state,
                _scalar_state(self, scale),
                trihedron.value,
                resolved_tolerance,
                resolved_continuity,
                resolved_max_degree,
                resolved_max_segments,
            ),
            operation_id="zencad.typed.sweep_surface",
        )
        return Surface._from_state(self, expression)

    def segment(self, start: Point3, end: Point3, /) -> Edge:
        _require_points(self, (start, end), minimum=2, name="segment")
        expression = self._expression(
            ops.segment,
            result=EDGE_SPEC,
            args=(start._state, end._state),
            operation_id="zencad.typed.segment",
        )
        return Edge._from_state(self, expression)

    def polysegment(
        self,
        points: Sequence[Point3],
        /,
        *,
        closed: bool = False,
    ) -> Wire:
        _require_bool(closed, "polysegment closed")
        values = _require_points(self, points, minimum=2, name="polysegment")
        expression = self._expression(
            ops.polysegment,
            result=WIRE_SPEC,
            args=(tuple(point._state for point in values), closed),
            operation_id="zencad.typed.polysegment",
        )
        return Wire._from_state(self, expression)

    @overload
    def polygon(
        self,
        points: Sequence[Point3],
        wire: Literal[False] = False,
    ) -> Face: ...

    @overload
    def polygon(
        self,
        points: Sequence[Point3],
        wire: Literal[True],
    ) -> Wire: ...

    @overload
    def polygon(self, points: Sequence[Point3], wire: bool) -> Face | Wire: ...

    def polygon(
        self,
        points: Sequence[Point3],
        wire: bool = False,
    ) -> Face | Wire:
        _require_bool(wire, "polygon wire")
        values = _require_points(self, points, minimum=3, name="polygon")
        if wire:
            return self.polysegment(values, closed=True)
        expression = self._expression(
            ops.polygon,
            result=FACE_SPEC,
            args=(tuple(point._state for point in values),),
            operation_id="zencad.typed.polygon",
        )
        return Face._from_state(self, expression)

    @overload
    def rectangle(
        self,
        a: ScalarInput,
        b: ScalarInput | None = None,
        center: bool = False,
        wire: Literal[False] = False,
    ) -> Face: ...

    @overload
    def rectangle(
        self,
        a: ScalarInput,
        b: ScalarInput | None = None,
        center: bool = False,
        *,
        wire: Literal[True],
    ) -> Wire: ...

    @overload
    def rectangle(
        self,
        a: ScalarInput,
        b: ScalarInput | None,
        center: bool,
        wire: Literal[True],
    ) -> Wire: ...

    @overload
    def rectangle(
        self,
        a: ScalarInput,
        b: ScalarInput | None,
        center: bool,
        wire: bool,
    ) -> Face | Wire: ...

    def rectangle(
        self,
        a: ScalarInput,
        b: ScalarInput | None = None,
        center: bool = False,
        wire: bool = False,
    ) -> Face | Wire:
        _require_bool(center, "rectangle center")
        _require_bool(wire, "rectangle wire")
        resolved_height = a if b is None else b
        if wire:
            return self.rectangle_wire(a, resolved_height, center)
        expression = self._expression(
            ops.rectangle,
            result=FACE_SPEC,
            args=(
                _scalar_state(self, a),
                _scalar_state(self, resolved_height),
                center,
            ),
            operation_id="zencad.typed.rectangle",
        )
        return Face._from_state(self, expression)

    def rectangle_wire(
        self,
        a: ScalarInput,
        b: ScalarInput,
        center: bool = False,
    ) -> Wire:
        _require_bool(center, "rectangle_wire center")
        x0 = -_as_scalar(self, a) / 2 if center else self.scalar(0)
        y0 = -_as_scalar(self, b) / 2 if center else self.scalar(0)
        width = _as_scalar(self, a)
        height = _as_scalar(self, b)
        return self.polysegment(
            (
                self.point3(x0, y0, 0),
                self.point3(x0 + width, y0, 0),
                self.point3(x0 + width, y0 + height, 0),
                self.point3(x0, y0 + height, 0),
            ),
            closed=True,
        )

    @overload
    def square(
        self,
        a: ScalarInput,
        b: ScalarInput | None = None,
        center: bool = False,
        wire: Literal[False] = False,
    ) -> Face: ...

    @overload
    def square(
        self,
        a: ScalarInput,
        b: ScalarInput | None = None,
        center: bool = False,
        *,
        wire: Literal[True],
    ) -> Wire: ...

    @overload
    def square(
        self,
        a: ScalarInput,
        b: ScalarInput | None,
        center: bool,
        wire: Literal[True],
    ) -> Wire: ...

    @overload
    def square(
        self,
        a: ScalarInput,
        b: ScalarInput | None,
        center: bool,
        wire: bool,
    ) -> Face | Wire: ...

    def square(
        self,
        a: ScalarInput,
        b: ScalarInput | None = None,
        center: bool = False,
        wire: bool = False,
    ) -> Face | Wire:
        return self.rectangle(a, b, center, wire)

    @overload
    def ngon(
        self,
        r: ScalarInput,
        n: int,
        wire: Literal[False] = False,
    ) -> Face: ...

    @overload
    def ngon(self, r: ScalarInput, n: int, wire: Literal[True]) -> Wire: ...

    @overload
    def ngon(self, r: ScalarInput, n: int, wire: bool) -> Face | Wire: ...

    def ngon(
        self,
        r: ScalarInput,
        n: int,
        wire: bool = False,
    ) -> Face | Wire:
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError("ngon n must be int")
        if n < 3:
            raise ValueError("ngon n must be at least 3")
        _require_bool(wire, "ngon wire")
        radius = _as_scalar(self, r)
        points = tuple(
            self.point3(
                radius * math.cos(2 * math.pi * index / n),
                radius * math.sin(2 * math.pi * index / n),
                0,
            )
            for index in range(n)
        )
        return self.polygon(points, wire)

    @overload
    def circle(
        self,
        r: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None = None,
        wire: Literal[False] = False,
    ) -> Face: ...

    @overload
    def circle(
        self,
        r: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None = None,
        *,
        wire: Literal[True],
    ) -> Edge: ...

    @overload
    def circle(
        self,
        r: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None,
        wire: Literal[True],
    ) -> Edge: ...

    @overload
    def circle(
        self,
        r: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None,
        wire: bool,
    ) -> Face | Edge: ...

    def circle(
        self,
        r: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None = None,
        wire: bool = False,
    ) -> Face | Edge:
        _require_bool(wire, "circle wire")
        expression = self._expression(
            ops.circle_shape,
            result=EDGE_SPEC if wire else FACE_SPEC,
            args=(
                _scalar_state(self, r),
                _angle_state(self, angle, "circle angle"),
                wire,
            ),
            operation_id="zencad.typed.face.circle",
        )
        if wire:
            return Edge._from_state(self, expression)
        return Face._from_state(self, expression)

    @overload
    def ellipse(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None = None,
        wire: Literal[False] = False,
    ) -> Face: ...

    @overload
    def ellipse(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None = None,
        *,
        wire: Literal[True],
    ) -> Edge: ...

    @overload
    def ellipse(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None,
        wire: Literal[True],
    ) -> Edge: ...

    @overload
    def ellipse(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None,
        wire: bool,
    ) -> Face | Edge: ...

    def ellipse(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        angle: ScalarInput | Sequence[ScalarInput] | None = None,
        wire: bool = False,
    ) -> Face | Edge:
        _require_bool(wire, "ellipse wire")
        expression = self._expression(
            ops.ellipse_shape,
            result=EDGE_SPEC if wire else FACE_SPEC,
            args=(
                _scalar_state(self, r1),
                _scalar_state(self, r2),
                _angle_state(self, angle, "ellipse angle"),
                wire,
            ),
            operation_id="zencad.typed.face.ellipse",
        )
        if wire:
            return Edge._from_state(self, expression)
        return Face._from_state(self, expression)

    def fill(self, shapes: Edge | Wire | Sequence[Edge | Wire], /) -> Face:
        values = _require_wire_parts(self, (shapes,), "fill")
        expression = self._expression(
            ops.fill_wires,
            result=FACE_SPEC,
            args=(tuple(shape._state for shape in values),),
            operation_id="zencad.typed.face.fill",
        )
        return Face._from_state(self, expression)

    def interpolate2(
        self,
        refs: Sequence[Sequence[Point3]],
        degmin: int = 3,
        degmax: int = 7,
    ) -> Face:
        if isinstance(refs, (str, bytes)) or not isinstance(refs, Sequence):
            raise TypeError("interpolate2 expects a point grid")
        rows = tuple(
            _require_points(self, row, minimum=2, name="interpolate2 row")
            for row in refs
        )
        if len(rows) < 2:
            raise ValueError("interpolate2 requires at least two rows")
        if len({len(row) for row in rows}) != 1:
            raise ValueError("interpolate2 point grid must be rectangular")
        degree_min = _require_positive_int(degmin, "interpolate2 degmin")
        degree_max = _require_positive_int(degmax, "interpolate2 degmax")
        if degree_min > degree_max:
            raise ValueError("interpolate2 degmin must not exceed degmax")
        expression = self._expression(
            ops.interpolate_face,
            result=FACE_SPEC,
            args=(
                tuple(tuple(point._state for point in row) for row in rows),
                degree_min,
                degree_max,
            ),
            operation_id="zencad.typed.face.interpolate2",
        )
        return Face._from_state(self, expression)

    def fix_face(self, shape: Face, /) -> Face:
        if not isinstance(shape, Face):
            raise TypeError("fix_face expects Face")
        require_same_runtime(self, shape)
        expression = self._expression(
            ops.fix_face,
            result=FACE_SPEC,
            args=(shape._state,),
            operation_id="zencad.typed.face.fix",
        )
        return Face._from_state(self, expression)

    def infplane(self) -> Face:
        expression = self._expression(
            ops.infinite_plane,
            result=FACE_SPEC,
            args=(),
            operation_id="zencad.typed.face.infplane",
        )
        return Face._from_state(self, expression)

    def ruled(self, first: Edge, second: Edge, /) -> Face:
        if not isinstance(first, Edge) or not isinstance(second, Edge):
            raise TypeError("ruled expects two Edge values")
        require_same_runtime(self, first)
        require_same_runtime(self, second)
        expression = self._expression(
            ops.ruled_face,
            result=FACE_SPEC,
            args=(first._state, second._state),
            operation_id="zencad.typed.face.ruled",
        )
        return Face._from_state(self, expression)

    def widewire(
        self,
        spine: Edge | Wire,
        r: ScalarInput,
        circled_joints: bool = True,
        circled_ends: bool = True,
    ) -> Shape:
        if not isinstance(spine, (Edge, Wire)):
            raise TypeError("widewire spine must be Edge or Wire")
        require_same_runtime(self, spine)
        _require_bool(circled_joints, "widewire circled_joints")
        _require_bool(circled_ends, "widewire circled_ends")
        expression = self._expression(
            ops.widewire,
            result=SHAPE_SPEC,
            args=(
                spine._state,
                _scalar_state(self, r),
                circled_joints,
                circled_ends,
            ),
            operation_id="zencad.typed.face.widewire",
        )
        return Shape._from_state(self, expression)

    def register_font(
        self,
        font_path: str | PathLike[str],
        aspect: FontAspect = FontAspect.UNDEFINED,
    ) -> None:
        """Immediately register a font in OCCT's process-wide font manager."""
        if not isinstance(font_path, (str, PathLike)):
            raise TypeError("register_font path must be str or PathLike")
        resolved_aspect = _require_font_aspect(aspect, "register_font aspect")
        text_ops.register_font(font_path, resolved_aspect.value)

    def text_to_brep(
        self,
        text: str,
        font_name: str,
        size: ScalarInput,
        aspect: FontAspect = FontAspect.REGULAR,
        composite_curve: bool = False,
    ) -> Compound:
        if not isinstance(text, str):
            raise TypeError("text_to_brep text must be str")
        if not isinstance(font_name, str):
            raise TypeError("text_to_brep font_name must be str")
        resolved_aspect = _require_font_aspect(aspect, "text_to_brep aspect")
        _require_bool(composite_curve, "text_to_brep composite_curve")
        expression = self._expression(
            text_ops.text_to_brep,
            result=COMPOUND_SPEC,
            args=(
                text,
                font_name,
                _scalar_state(self, size),
                resolved_aspect.value,
                composite_curve,
            ),
            operation_id="zencad.typed.text_to_brep",
            cacheable=False,
        )
        return Compound._from_state(self, expression)

    def textshape(
        self,
        text: str,
        fontname: str,
        size: ScalarInput,
        composite_curve: bool = False,
    ) -> Compound:
        """Legacy spelling for :meth:`text_to_brep`."""
        return self.text_to_brep(
            text,
            fontname,
            size,
            FontAspect.REGULAR,
            composite_curve,
        )

    def make_shell(self, faces: Face | Sequence[Face], /) -> Shell:
        values = _require_faces(self, faces, "make_shell")
        expression = self._expression(
            ops.make_shell,
            result=SHELL_SPEC,
            args=(tuple(face._state for face in values),),
            operation_id="zencad.typed.make_shell",
        )
        return Shell._from_state(self, expression)

    def fill3d(self, shell: Shell, /) -> Solid:
        if not isinstance(shell, Shell):
            raise TypeError("fill3d expects Shell")
        require_same_runtime(self, shell)
        expression = self._expression(
            ops.fill_shell,
            result=SOLID_SPEC,
            args=(shell._state,),
            operation_id="zencad.typed.fill3d",
        )
        return Solid._from_state(self, expression)

    def polyhedron_shell(
        self,
        pnts: Sequence[Point3],
        faces_no: Sequence[Sequence[int]],
    ) -> Shell:
        points = _require_points(self, pnts, minimum=3, name="polyhedron_shell")
        faces = _require_polyhedron_faces(faces_no, len(points), "polyhedron_shell")
        expression = self._expression(
            ops.polyhedron_shell,
            result=SHELL_SPEC,
            args=(tuple(point._state for point in points), faces),
            operation_id="zencad.typed.polyhedron_shell",
        )
        return Shell._from_state(self, expression)

    @overload
    def polyhedron(
        self,
        pnts: Sequence[Point3],
        faces: Sequence[Sequence[int]],
        shell: Literal[False] = False,
    ) -> Solid: ...

    @overload
    def polyhedron(
        self,
        pnts: Sequence[Point3],
        faces: Sequence[Sequence[int]],
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def polyhedron(
        self,
        pnts: Sequence[Point3],
        faces: Sequence[Sequence[int]],
        shell: bool,
    ) -> Solid | Shell: ...

    def polyhedron(
        self,
        pnts: Sequence[Point3],
        faces: Sequence[Sequence[int]],
        shell: bool = False,
    ) -> Solid | Shell:
        _require_bool(shell, "polyhedron shell")
        result = self.polyhedron_shell(pnts, faces)
        if shell:
            return result
        return self.fill3d(result)

    def convex_hull(
        self,
        pnts: Sequence[Point3],
        incremental: bool = False,
        qhull_options: str | None = None,
    ) -> tuple[tuple[int, ...], ...]:
        """Materialize the numeric triangulation returned by SciPy/Qhull."""
        points = _require_points(self, pnts, minimum=4, name="convex_hull")
        _require_bool(incremental, "convex_hull incremental")
        options = _require_qhull_options(qhull_options, "convex_hull")
        return ops.convex_hull_faces(
            tuple(point._resolved() for point in points),
            incremental,
            options,
        )

    @overload
    def convex_hull_shape(
        self,
        pnts: Sequence[Point3],
        shell: Literal[False] = False,
        incremental: bool = False,
        qhull_options: str | None = None,
    ) -> Solid: ...

    @overload
    def convex_hull_shape(
        self,
        pnts: Sequence[Point3],
        shell: Literal[True],
        incremental: bool = False,
        qhull_options: str | None = None,
    ) -> Shell: ...

    @overload
    def convex_hull_shape(
        self,
        pnts: Sequence[Point3],
        shell: bool,
        incremental: bool = False,
        qhull_options: str | None = None,
    ) -> Solid | Shell: ...

    def convex_hull_shape(
        self,
        pnts: Sequence[Point3],
        shell: bool = False,
        incremental: bool = False,
        qhull_options: str | None = None,
    ) -> Solid | Shell:
        points = _require_points(self, pnts, minimum=4, name="convex_hull_shape")
        _require_bool(shell, "convex_hull_shape shell")
        _require_bool(incremental, "convex_hull_shape incremental")
        options = _require_qhull_options(qhull_options, "convex_hull_shape")
        expression = self._expression(
            ops.convex_hull_shape,
            result=SHELL_SPEC if shell else SOLID_SPEC,
            args=(
                tuple(point._state for point in points),
                incremental,
                options,
                shell,
            ),
            operation_id="zencad.typed.convex_hull_shape",
        )
        if shell:
            return Shell._from_state(self, expression)
        return Solid._from_state(self, expression)

    @overload
    def tetrahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: Literal[False] = False,
    ) -> Solid: ...

    @overload
    def tetrahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        *,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def tetrahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def tetrahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: bool,
    ) -> Solid | Shell: ...

    def tetrahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: bool = False,
    ) -> Solid | Shell:
        _require_bool(shell, "tetrahedron shell")
        edge = (
            _as_scalar(self, a)
            if a is not None
            else _as_scalar(self, r) / math.sqrt(3 / 2) * 2
        )
        half_edge = edge / 2
        face_inradius = edge * math.sqrt(3) / 6
        face_circumradius = edge * math.sqrt(3) / 3
        inradius = edge * math.sqrt(6) / 12
        circumradius = edge * math.sqrt(6) / 4
        return _platonic_polyhedron(
            self,
            (
                (0, 0, circumradius),
                (0, face_circumradius, -inradius),
                (-half_edge, -face_inradius, -inradius),
                (half_edge, -face_inradius, -inradius),
            ),
            ((1, 0, 3), (2, 0, 1), (3, 0, 2), (2, 1, 3)),
            shell,
        )

    @overload
    def hexahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: Literal[False] = False,
    ) -> Solid: ...

    @overload
    def hexahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        *,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def hexahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def hexahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: bool,
    ) -> Solid | Shell: ...

    def hexahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: bool = False,
    ) -> Solid | Shell:
        _require_bool(shell, "hexahedron shell")
        edge = (
            _as_scalar(self, a)
            if a is not None
            else _as_scalar(self, r) / math.sqrt(3) * 2
        )
        half_edge = edge / 2
        return _platonic_polyhedron(
            self,
            (
                (-half_edge, -half_edge, -half_edge),
                (-half_edge, -half_edge, half_edge),
                (-half_edge, half_edge, -half_edge),
                (-half_edge, half_edge, half_edge),
                (half_edge, -half_edge, -half_edge),
                (half_edge, -half_edge, half_edge),
                (half_edge, half_edge, -half_edge),
                (half_edge, half_edge, half_edge),
            ),
            (
                (0, 1, 3, 2),
                (4, 5, 7, 6),
                (2, 3, 7, 6),
                (0, 1, 5, 4),
                (0, 2, 6, 4),
                (1, 3, 7, 5),
            ),
            shell,
        )

    @overload
    def octahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: Literal[False] = False,
    ) -> Solid: ...

    @overload
    def octahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        *,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def octahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def octahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: bool,
    ) -> Solid | Shell: ...

    def octahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: bool = False,
    ) -> Solid | Shell:
        _require_bool(shell, "octahedron shell")
        edge = (
            _as_scalar(self, a)
            if a is not None
            else _as_scalar(self, r) / math.sqrt(2) * 2
        )
        half_edge = edge / 2
        circumradius = edge * math.sqrt(2) / 2
        return _platonic_polyhedron(
            self,
            (
                (0, 0, circumradius),
                (-half_edge, half_edge, 0),
                (half_edge, half_edge, 0),
                (half_edge, -half_edge, 0),
                (-half_edge, -half_edge, 0),
                (0, 0, -circumradius),
            ),
            (
                (1, 0, 2),
                (2, 0, 3),
                (3, 0, 4),
                (4, 0, 1),
                (5, 1, 2),
                (5, 2, 3),
                (5, 3, 4),
                (4, 1, 5),
            ),
            shell,
        )

    @overload
    def dodecahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: Literal[False] = False,
    ) -> Solid: ...

    @overload
    def dodecahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        *,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def dodecahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def dodecahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: bool,
    ) -> Solid | Shell: ...

    def dodecahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: bool = False,
    ) -> Solid | Shell:
        _require_bool(shell, "dodecahedron shell")
        edge = (
            _as_scalar(self, a)
            if a is not None
            else _as_scalar(self, r) / (math.sqrt(3) * (1 + math.sqrt(5)) / 2) * 2
        )
        cube = edge * (1 + math.sqrt(5)) / 4
        zero = edge * 0
        cuboid = edge * (3 + math.sqrt(5)) / 4
        half_edge = edge / 2
        return _platonic_polyhedron(
            self,
            (
                (zero, cuboid, half_edge),
                (zero, cuboid, -half_edge),
                (zero, -cuboid, half_edge),
                (zero, -cuboid, -half_edge),
                (half_edge, zero, cuboid),
                (half_edge, zero, -cuboid),
                (-half_edge, zero, cuboid),
                (-half_edge, zero, -cuboid),
                (cube, cube, cube),
                (cube, cube, -cube),
                (cube, -cube, cube),
                (cube, -cube, -cube),
                (-cube, cube, cube),
                (-cube, cube, -cube),
                (-cube, -cube, cube),
                (-cube, -cube, -cube),
                (cuboid, half_edge, zero),
                (cuboid, -half_edge, zero),
                (-cuboid, half_edge, zero),
                (-cuboid, -half_edge, zero),
            ),
            (
                (8, 16, 9, 1, 0),
                (12, 6, 4, 8, 0),
                (1, 13, 18, 12, 0),
                (9, 5, 7, 13, 1),
                (14, 19, 15, 3, 2),
                (3, 11, 17, 10, 2),
                (10, 4, 6, 14, 2),
                (15, 7, 5, 11, 3),
                (10, 17, 16, 8, 4),
                (9, 16, 17, 11, 5),
                (12, 18, 19, 14, 6),
                (15, 19, 18, 13, 7),
            ),
            shell,
        )

    @overload
    def icosahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: Literal[False] = False,
    ) -> Solid: ...

    @overload
    def icosahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        *,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def icosahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def icosahedron(
        self,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: bool,
    ) -> Solid | Shell: ...

    def icosahedron(
        self,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: bool = False,
    ) -> Solid | Shell:
        _require_bool(shell, "icosahedron shell")
        edge = (
            _as_scalar(self, a)
            if a is not None
            else _as_scalar(self, r)
            / (math.sqrt((5 - math.sqrt(5)) / 2) * (1 + math.sqrt(5)) / 2)
            * 2
        )
        zero = edge * 0
        half_edge = edge / 2
        golden = edge * (1 + math.sqrt(5)) / 4
        return _platonic_polyhedron(
            self,
            (
                (golden, zero, half_edge),
                (golden, zero, -half_edge),
                (-golden, zero, half_edge),
                (-golden, zero, -half_edge),
                (half_edge, golden, zero),
                (half_edge, -golden, zero),
                (-half_edge, golden, zero),
                (-half_edge, -golden, zero),
                (zero, half_edge, golden),
                (zero, half_edge, -golden),
                (zero, -half_edge, golden),
                (zero, -half_edge, -golden),
            ),
            (
                (1, 0, 5),
                (4, 0, 1),
                (5, 0, 10),
                (8, 0, 4),
                (10, 0, 8),
                (4, 1, 9),
                (9, 1, 11),
                (11, 1, 5),
                (3, 2, 6),
                (6, 2, 8),
                (7, 2, 3),
                (8, 2, 10),
                (10, 2, 7),
                (7, 3, 11),
                (9, 3, 6),
                (11, 3, 9),
                (6, 4, 9),
                (8, 4, 6),
                (7, 5, 10),
                (11, 5, 7),
            ),
            shell,
        )

    @overload
    def platonic(
        self,
        nfaces: int,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: Literal[False] = False,
    ) -> Solid: ...

    @overload
    def platonic(
        self,
        nfaces: int,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        *,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def platonic(
        self,
        nfaces: int,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: Literal[True],
    ) -> Shell: ...

    @overload
    def platonic(
        self,
        nfaces: int,
        r: ScalarInput,
        a: ScalarInput | None,
        shell: bool,
    ) -> Solid | Shell: ...

    def platonic(
        self,
        nfaces: int,
        r: ScalarInput = 1,
        a: ScalarInput | None = None,
        shell: bool = False,
    ) -> Solid | Shell:
        if isinstance(nfaces, bool) or not isinstance(nfaces, int):
            raise TypeError("platonic nfaces must be int")
        _require_bool(shell, "platonic shell")
        factories = {
            4: self.tetrahedron,
            6: self.hexahedron,
            8: self.octahedron,
            12: self.dodecahedron,
            20: self.icosahedron,
        }
        try:
            factory = factories[nfaces]
        except KeyError as exception:
            raise ValueError(
                "platonic nfaces must be one of 4, 6, 8, 12, 20"
            ) from exception
        return factory(r, a, shell)

    def point(self, x: ScalarInput, y: ScalarInput, z: ScalarInput) -> Point3:
        return Point3(x, y, z, runtime=self)

    def vector(self, x: ScalarInput, y: ScalarInput, z: ScalarInput) -> Vector3:
        return Vector3(x, y, z, runtime=self)

    def scalar(self, value: Number) -> Scalar:
        return Scalar(value, runtime=self)

    def point2(self, x: ScalarInput, y: ScalarInput) -> Point2:
        return Point2(x, y, runtime=self)

    def vector2(self, x: ScalarInput, y: ScalarInput) -> Vector2:
        return Vector2(x, y, runtime=self)

    def quaternion(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        w: ScalarInput,
    ) -> Quaternion:
        return Quaternion(x, y, z, w, runtime=self)

    @overload
    def point3(self) -> Point3: ...

    @overload
    def point3(self, value: Point3 | Vector3 | Sequence[ScalarInput], /) -> Point3: ...

    @overload
    def point3(
        self,
        x: ScalarInput,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        /,
    ) -> Point3: ...

    def point3(self, *args: object) -> Point3:
        """Compatibility constructor with legacy coordinate padding."""
        if len(args) == 1 and isinstance(args[0], Point3):
            require_same_runtime(self, args[0])
            return args[0]
        components = _compat_components3(self, args, "point3")
        return Point3(*components, runtime=self)

    @overload
    def vector3(self) -> Vector3: ...

    @overload
    def vector3(
        self,
        value: Point3 | Vector3 | Sequence[ScalarInput],
        /,
    ) -> Vector3: ...

    @overload
    def vector3(
        self,
        x: ScalarInput,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        /,
    ) -> Vector3: ...

    def vector3(self, *args: object) -> Vector3:
        """Compatibility constructor with legacy coordinate padding."""
        if len(args) == 1 and isinstance(args[0], Vector3):
            require_same_runtime(self, args[0])
            return args[0]
        components = _compat_components3(self, args, "vector3")
        return Vector3(*components, runtime=self)

    @overload
    def quat(self, value: Quaternion | gp_Quaternion, /) -> Quaternion: ...

    @overload
    def quat(
        self,
        values: Sequence[ScalarInput],
        /,
    ) -> Quaternion: ...

    @overload
    def quat(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        w: ScalarInput,
        /,
    ) -> Quaternion: ...

    def quat(self, *args: object) -> Quaternion:
        """Compatibility quaternion constructor returning the stable handle."""
        if len(args) == 1:
            value = args[0]
            if isinstance(value, Quaternion):
                require_same_runtime(self, value)
                return value
            if isinstance(value, gp_Quaternion):
                return Quaternion.from_ocp(value, runtime=self)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                args = tuple(value)
        if len(args) != 4:
            raise TypeError(
                "quat expects Quaternion, gp_Quaternion, or four components"
            )
        return Quaternion(
            cast(ScalarInput, args[0]),
            cast(ScalarInput, args[1]),
            cast(ScalarInput, args[2]),
            cast(ScalarInput, args[3]),
            runtime=self,
        )

    def points(self, values: Sequence[object], /) -> list[Point3]:
        return [self.point3(value) for value in values]

    def points2(self, values: Sequence[Sequence[object]], /) -> list[list[Point3]]:
        return [self.points(value) for value in values]

    def vectors(self, values: Sequence[object], /) -> list[Vector3]:
        return [self.vector3(value) for value in values]

    def to_Vertex(self, value: object, /) -> TopoDS_Vertex:
        return self.point3(value).Vtx()

    def to_GeomPoint(self, value: object, /) -> Geom_CartesianPoint:
        return Geom_CartesianPoint(self.point3(value).Pnt())

    def quaternion_axis_angle(
        self,
        axis: Vector3,
        angle: ScalarInput,
        /,
    ) -> Quaternion:
        if not isinstance(axis, Vector3):
            raise TypeError("quaternion_axis_angle expects Vector3")
        require_same_runtime(self, axis)
        state = self._value_state(
            transform_ops.quaternion_axis_angle,
            result=QUATERNION_SPEC,
            args=(axis._state, _scalar_state(self, angle)),
            operation_id="zencad.typed.quaternion.axis_angle",
        )
        return Quaternion._from_state(self, state)

    def identity_transform(self) -> Transform:
        return Transform(runtime=self)

    def identity_affine_transform(self) -> AffineTransform:
        return AffineTransform(runtime=self)

    def affine_transform(
        self,
        rows: Sequence[Sequence[ScalarInput]],
        /,
    ) -> AffineTransform:
        return AffineTransform(rows, runtime=self)

    def affine(
        self,
        rows: Sequence[Sequence[ScalarInput]],
        /,
    ) -> AffineTransform:
        return self.affine_transform(rows)

    def nulltrans(self) -> Transform:
        return self.identity_transform()

    @overload
    def translation(self, vector: Vector3, /) -> Transform: ...

    @overload
    def translation(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        /,
    ) -> Transform: ...

    def translation(self, *args: object) -> Transform:
        if len(args) == 1 and isinstance(args[0], Vector3):
            vector = args[0]
            require_same_runtime(self, vector)
        elif len(args) == 3:
            vector = Vector3(
                cast(ScalarInput, args[0]),
                cast(ScalarInput, args[1]),
                cast(ScalarInput, args[2]),
                runtime=self,
            )
        else:
            raise TypeError("translation expects Vector3 or three scalar coordinates")
        state = self._value_state(
            transform_ops.translation_transform,
            result=TRANSFORM_SPEC,
            args=(vector._state,),
            operation_id="zencad.typed.transform.translation",
        )
        return Transform._from_state(self, state)

    def move(self, *args: object) -> Transform:
        return self.translation(self.vector3(*args))

    def translate(self, *args: object) -> Transform:
        return self.move(*args)

    def moveX(self, value: ScalarInput, /) -> Transform:
        return self.translation(value, 0, 0)

    def moveY(self, value: ScalarInput, /) -> Transform:
        return self.translation(0, value, 0)

    def moveZ(self, value: ScalarInput, /) -> Transform:
        return self.translation(0, 0, value)

    def movX(self, value: ScalarInput, /) -> Transform:
        return self.moveX(value)

    def movY(self, value: ScalarInput, /) -> Transform:
        return self.moveY(value)

    def movZ(self, value: ScalarInput, /) -> Transform:
        return self.moveZ(value)

    def translateX(self, value: ScalarInput, /) -> Transform:
        return self.moveX(value)

    def translateY(self, value: ScalarInput, /) -> Transform:
        return self.moveY(value)

    def translateZ(self, value: ScalarInput, /) -> Transform:
        return self.moveZ(value)

    def right(self, value: ScalarInput, /) -> Transform:
        return self.moveX(value)

    def left(self, value: ScalarInput, /) -> Transform:
        return self.moveX(-_as_scalar(self, value))

    def forw(self, value: ScalarInput, /) -> Transform:
        return self.moveY(value)

    def back(self, value: ScalarInput, /) -> Transform:
        return self.moveY(-_as_scalar(self, value))

    def up(self, value: ScalarInput, /) -> Transform:
        return self.moveZ(value)

    def down(self, value: ScalarInput, /) -> Transform:
        return self.moveZ(-_as_scalar(self, value))

    @overload
    def rotation(self, quaternion: Quaternion, /) -> Transform: ...

    @overload
    def rotation(
        self,
        axis: Vector3,
        angle: ScalarInput,
        /,
    ) -> Transform: ...

    def rotation(self, *args: object) -> Transform:
        if len(args) == 1 and isinstance(args[0], Quaternion):
            quaternion = args[0]
            require_same_runtime(self, quaternion)
        elif len(args) == 2 and isinstance(args[0], Vector3):
            quaternion = self.quaternion_axis_angle(args[0], cast(ScalarInput, args[1]))
        else:
            raise TypeError("rotation expects Quaternion or Vector3 and angle")
        return quaternion.to_transform()

    def rotate(
        self,
        axis: Vector3 | Sequence[ScalarInput],
        angle: ScalarInput | None = None,
        /,
    ) -> Transform:
        resolved_axis = self.vector3(axis)
        if angle is None:
            angle = resolved_axis.length()
            resolved_axis = resolved_axis.normalized()
        return self.rotation(resolved_axis, angle)

    def rotate_quat(
        self,
        quaternion: Quaternion | gp_Quaternion | Sequence[ScalarInput],
        /,
    ) -> Transform:
        return self.rotation(self.quat(quaternion))

    def rotateX(self, angle: ScalarInput, /) -> Transform:
        return self.rotation(self.vector3(1, 0, 0), angle)

    def rotateY(self, angle: ScalarInput, /) -> Transform:
        return self.rotation(self.vector3(0, 1, 0), angle)

    def rotateZ(self, angle: ScalarInput, /) -> Transform:
        return self.rotation(self.vector3(0, 0, 1), angle)

    def scale(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> Transform:
        if center is None:
            center = self.point(0, 0, 0)
        elif not isinstance(center, Point3):
            raise TypeError("scale center must be Point3")
        require_same_runtime(self, center)
        state = self._value_state(
            transform_ops.scale_transform,
            result=TRANSFORM_SPEC,
            args=(_scalar_state(self, factor), center._state),
            operation_id="zencad.typed.transform.scale",
        )
        return Transform._from_state(self, state)

    def scaleXYZ(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> AffineTransform:
        if center is None:
            center = self.point(0, 0, 0)
        elif not isinstance(center, Point3):
            raise TypeError("affine scale center must be Point3")
        require_same_runtime(self, center)
        state = self._value_state(
            transform_ops.affine_scale_transform,
            result=AFFINE_TRANSFORM_SPEC,
            args=(
                _scalar_state(self, x),
                _scalar_state(self, y),
                _scalar_state(self, z),
                center._state,
            ),
            operation_id="zencad.typed.affine.scale_xyz",
        )
        return AffineTransform._from_state(self, state)

    def scaleX(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> AffineTransform:
        return self.scaleXYZ(factor, 1, 1, center=center)

    def scaleY(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> AffineTransform:
        return self.scaleXYZ(1, factor, 1, center=center)

    def scaleZ(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> AffineTransform:
        return self.scaleXYZ(1, 1, factor, center=center)

    def mirror(
        self,
        normal: Vector3,
        /,
        *,
        origin: Point3 | None = None,
    ) -> Transform:
        if not isinstance(normal, Vector3):
            raise TypeError("mirror normal must be Vector3")
        if origin is None:
            origin = self.point(0, 0, 0)
        elif not isinstance(origin, Point3):
            raise TypeError("mirror origin must be Point3")
        require_same_runtime(self, normal)
        require_same_runtime(self, origin)
        state = self._value_state(
            transform_ops.mirror_transform,
            result=TRANSFORM_SPEC,
            args=(normal._state, origin._state),
            operation_id="zencad.typed.transform.mirror",
        )
        return Transform._from_state(self, state)

    def mirror_plane(self, *normal: object) -> Transform:
        return self.mirror(self.vector3(*normal))

    def mirrorXY(self) -> Transform:
        return self.mirror_plane(0, 0, 1)

    def mirrorYZ(self) -> Transform:
        return self.mirror_plane(1, 0, 0)

    def mirrorXZ(self) -> Transform:
        return self.mirror_plane(0, 1, 0)

    def mirror_axis(self, *axis: object) -> Transform:
        return self.rotation(self.vector3(*axis), math.pi)

    def mirrorX(self) -> Transform:
        return self.mirror_axis(1, 0, 0)

    def mirrorY(self) -> Transform:
        return self.mirror_axis(0, 1, 0)

    def mirrorZ(self) -> Transform:
        return self.mirror_axis(0, 0, 1)

    def mirrorO(self, *origin: object) -> Transform:
        return self.scale(-1, center=self.point3(*origin))

    def multitransform(
        self,
        transforms: Sequence[Transform],
        array: bool = False,
        unit: bool = False,
    ) -> MultiTransform:
        return MultiTransform(transforms, runtime=self, array=array, unit=unit)

    def multitrans(
        self,
        transforms: Sequence[Transform],
        array: bool = False,
        unit: bool = False,
    ) -> MultiTransform:
        return self.multitransform(transforms, array, unit)

    def sqrmirror(
        self,
        array: bool = False,
        unit: bool = False,
    ) -> MultiTransform:
        return self.multitransform(
            (self.nulltrans(), self.mirrorYZ(), self.mirrorXZ(), self.mirrorZ()),
            array,
            unit,
        )

    def sqrtrans(
        self,
        array: bool = False,
        unit: bool = False,
    ) -> MultiTransform:
        return self.sqrmirror(array, unit)

    def rotate_array(
        self,
        n: int,
        yaw: ScalarInput = 2 * math.pi,
        endpoint: bool = False,
        array: bool = False,
        unit: bool = False,
    ) -> MultiTransform:
        fractions = _sample_fractions(n, endpoint)
        transforms = [self.rotateZ(_as_scalar(self, yaw) * item) for item in fractions]
        return self.multitransform(transforms, array, unit)

    def rotate_array2(
        self,
        n: int,
        r: ScalarInput | None = None,
        yaw: tuple[ScalarInput, ScalarInput] = (0, 2 * math.pi),
        roll: tuple[ScalarInput, ScalarInput] = (0, 0),
        endpoint: bool = False,
        array: bool = False,
        unit: bool = False,
    ) -> MultiTransform:
        fractions = _sample_fractions(n, endpoint)
        yaw_values = _sample_scalar_range(self, yaw, fractions, "yaw")
        roll_values = _sample_scalar_range(self, roll, fractions, "roll")
        radius: ScalarInput = 0 if r is None else r
        transforms = [
            self.rotateZ(yaw_value)
            * self.right(radius)
            * self.rotateX(math.pi / 2)
            * self.rotateZ(roll_value)
            for yaw_value, roll_value in zip(yaw_values, roll_values)
        ]
        return self.multitransform(transforms, array, unit)

    def short_rotate(
        self,
        source: Vector3 | Sequence[ScalarInput],
        target: Vector3 | Sequence[ScalarInput],
        /,
    ) -> Transform:
        resolved_source = self.vector3(source)
        resolved_target = self.vector3(target)
        state = self._value_state(
            transform_ops.shortest_rotation_transform,
            result=TRANSFORM_SPEC,
            args=(resolved_source._state, resolved_target._state),
            operation_id="zencad.typed.transform.shortest_rotation",
        )
        return Transform._from_state(self, state)


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_font_aspect(value: object, name: str) -> FontAspect:
    if not isinstance(value, FontAspect):
        raise TypeError(f"{name} must be FontAspect")
    return value


def _require_center(
    value: bool | str | None,
    name: str,
) -> bool | str | None:
    if value is not None and not isinstance(value, (bool, str)):
        raise TypeError(f"{name} must be bool, str, or None")
    return value


def _optional_scalar_state(
    runtime: Runtime,
    value: ScalarInput | None,
) -> State[float] | None:
    if value is None:
        return None
    return _scalar_state(runtime, value)


def _angle_state(
    runtime: Runtime,
    value: ScalarInput | Sequence[ScalarInput] | None,
    name: str,
) -> State[float] | tuple[State[float], State[float]] | None:
    if value is None:
        return None
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values = tuple(value)
        if len(values) != 2:
            raise TypeError(f"{name} must contain exactly two scalar bounds")
        return (
            _scalar_state(runtime, values[0]),
            _scalar_state(runtime, values[1]),
        )
    return _scalar_state(runtime, cast(ScalarInput, value))


def _box_size(
    runtime: Runtime,
    x: ScalarInput | Vector3 | Sequence[ScalarInput],
    y: ScalarInput | None,
    z: ScalarInput | None,
    size: ScalarInput | Vector3 | Sequence[ScalarInput] | None,
) -> Vector3:
    source = x if size is None else size
    if size is not None:
        y = None
        z = None
    if isinstance(source, Vector3):
        if y is not None or z is not None:
            raise TypeError("box Vector3 size cannot be combined with y or z")
        require_same_runtime(runtime, source)
        return source
    if isinstance(source, Sequence) and not isinstance(source, (str, bytes)):
        if y is not None or z is not None:
            raise TypeError("box sequence size cannot be combined with y or z")
        values = tuple(source)
        if len(values) != 3:
            raise TypeError("box size must contain exactly three dimensions")
        return runtime.vector(values[0], values[1], values[2])
    scalar = cast(ScalarInput, source)
    if y is None and z is None:
        return runtime.vector(scalar, scalar, scalar)
    if y is not None and z is not None:
        return runtime.vector(scalar, y, z)
    raise TypeError("box expects one size or all three dimensions")


def _require_shells(
    runtime: Runtime,
    shells: Shell | Sequence[Shell],
    name: str,
) -> tuple[Shell, ...]:
    values: tuple[Shell, ...]
    if isinstance(shells, Shell):
        values = (shells,)
    elif isinstance(shells, Sequence) and not isinstance(shells, (str, bytes)):
        values = tuple(shells)
    else:
        raise TypeError(f"{name} expects Shell or a sequence of Shell")
    if not values:
        raise ValueError(f"{name} requires at least one Shell")
    if not all(isinstance(shell, Shell) for shell in values):
        raise TypeError(f"{name} expects only Shell values")
    for shell in values:
        require_same_runtime(runtime, shell)
    return values


def _require_shapes(
    runtime: Runtime,
    shapes: Shape | Sequence[Shape],
    others: tuple[Shape, ...],
    name: str,
) -> tuple[Shape, ...]:
    if isinstance(shapes, Shape):
        values = (shapes, *others)
    elif isinstance(shapes, Sequence) and not isinstance(shapes, (str, bytes)):
        if others:
            raise TypeError(f"{name} cannot combine a Shape sequence with extra operands")
        values = tuple(shapes)
    else:
        raise TypeError(f"{name} expects Shape operands or a sequence of Shape")
    if not values:
        raise ValueError(f"{name} requires at least one Shape")
    if not all(isinstance(shape, Shape) for shape in values):
        raise TypeError(f"{name} expects only Shape operands")
    for shape in values:
        require_same_runtime(runtime, shape)
    return values


def _section_operand(
    runtime: Runtime,
    value: Shape | ScalarInput | Point3 | Vector3 | Sequence[ScalarInput],
    name: str,
) -> Shape:
    if isinstance(value, Shape):
        require_same_runtime(runtime, value)
        return value
    if isinstance(value, (Point3, Vector3)):
        direction = runtime.vector3(value)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        coordinates = tuple(value)
        if len(coordinates) != 3:
            raise TypeError(f"{name} plane vector must contain three coordinates")
        direction = runtime.vector3(coordinates)
    else:
        return runtime.halfspace().up(cast(ScalarInput, value))
    transform = runtime.translation(direction) * runtime.short_rotate(
        runtime.vector3(0, 0, 1), direction
    )
    return runtime.halfspace().transform(transform)


def _require_faces(
    runtime: Runtime,
    faces: Face | Sequence[Face],
    name: str,
) -> tuple[Face, ...]:
    values: tuple[Face, ...]
    if isinstance(faces, Face):
        values = (faces,)
    elif isinstance(faces, Sequence) and not isinstance(faces, (str, bytes)):
        values = tuple(faces)
    else:
        raise TypeError(f"{name} expects Face or a sequence of Face")
    if not values:
        raise ValueError(f"{name} requires at least one Face")
    if not all(isinstance(face, Face) for face in values):
        raise TypeError(f"{name} expects only Face values")
    for face in values:
        require_same_runtime(runtime, face)
    return values


def _require_polyhedron_faces(
    faces: Sequence[Sequence[int]],
    point_count: int,
    name: str,
) -> tuple[tuple[int, ...], ...]:
    if isinstance(faces, (str, bytes)) or not isinstance(faces, Sequence):
        raise TypeError(f"{name} faces must be a sequence")
    result: list[tuple[int, ...]] = []
    for face in faces:
        if isinstance(face, (str, bytes)) or not isinstance(face, Sequence):
            raise TypeError(f"{name} faces must contain index sequences")
        indices = tuple(face)
        if len(indices) < 3:
            raise ValueError(f"{name} faces must contain at least three indices")
        if not all(
            isinstance(index, int) and not isinstance(index, bool) for index in indices
        ):
            raise TypeError(f"{name} face indices must be int")
        if any(index < 0 or index >= point_count for index in indices):
            raise IndexError(f"{name} face index is outside the point sequence")
        result.append(indices)
    if not result:
        raise ValueError(f"{name} requires at least one face")
    return tuple(result)


def _require_qhull_options(value: str | None, name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{name} qhull_options must be str or None")
    return value


def _platonic_polyhedron(
    runtime: Runtime,
    coordinates: Sequence[tuple[ScalarInput, ScalarInput, ScalarInput]],
    faces: Sequence[Sequence[int]],
    shell: bool,
) -> Solid | Shell:
    points = tuple(runtime.point3(*coordinate) for coordinate in coordinates)
    return runtime.polyhedron(points, faces, shell)


def _require_tangents(
    runtime: Runtime,
    tangents: Sequence[Vector3 | None] | None,
    point_count: int,
    name: str,
) -> tuple[Vector3 | None, ...] | None:
    if tangents is None:
        return None
    if isinstance(tangents, (str, bytes)) or not isinstance(tangents, Sequence):
        raise TypeError(f"{name} tangents must be a sequence")
    values = tuple(tangents)
    if len(values) != point_count:
        raise ValueError(f"{name} tangents must match point count")
    if not all(tangent is None or isinstance(tangent, Vector3) for tangent in values):
        raise TypeError(f"{name} tangents must contain only Vector3 or None")
    for tangent in values:
        if tangent is not None:
            require_same_runtime(runtime, tangent)
    return values


def _scalar_sequence_state(
    runtime: Runtime,
    values: Sequence[ScalarInput],
    name: str,
) -> tuple[State[float], ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be a scalar sequence")
    result = tuple(_scalar_state(runtime, value) for value in values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _optional_scalar_sequence_state(
    runtime: Runtime,
    values: Sequence[ScalarInput] | None,
    name: str,
) -> tuple[State[float], ...] | None:
    if values is None:
        return None
    return _scalar_sequence_state(runtime, values, name)


def _int_sequence(values: Sequence[int], name: str) -> tuple[int, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be an int sequence")
    result = tuple(values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    if not all(
        isinstance(value, int) and not isinstance(value, bool) for value in result
    ):
        raise TypeError(f"{name} must contain only int values")
    return result


def _interval_state(
    runtime: Runtime,
    interval: Interval | Sequence[ScalarInput] | None,
    name: str,
) -> tuple[State[float], State[float]] | None:
    if interval is None:
        return None
    if isinstance(interval, Interval):
        require_same_runtime(runtime, interval.lower)
        return (interval.lower._state, interval.upper._state)
    if isinstance(interval, (str, bytes)) or not isinstance(interval, Sequence):
        raise TypeError(f"{name} must contain two scalar bounds")
    values = tuple(interval)
    if len(values) != 2:
        raise TypeError(f"{name} must contain two scalar bounds")
    return (_scalar_state(runtime, values[0]), _scalar_state(runtime, values[1]))


def _require_wire_parts(
    runtime: Runtime,
    shapes: tuple[Edge | Wire | Sequence[Edge | Wire], ...],
    name: str,
) -> tuple[Edge | Wire, ...]:
    if len(shapes) == 1 and isinstance(shapes[0], Sequence):
        candidate = shapes[0]
        if isinstance(candidate, (str, bytes)):
            raise TypeError(f"{name} expects Edge or Wire handles")
        values = tuple(candidate)
    else:
        values = cast(tuple[Edge | Wire, ...], shapes)
    if not values:
        raise ValueError(f"{name} requires at least one Edge or Wire")
    if not all(isinstance(shape, (Edge, Wire)) for shape in values):
        raise TypeError(f"{name} accepts only Edge or Wire handles")
    for shape in values:
        require_same_runtime(runtime, shape)
    return values


def _as_scalar(runtime: Runtime, value: ScalarInput) -> Scalar:
    if isinstance(value, Scalar):
        require_same_runtime(runtime, value)
        return value
    return runtime.scalar(value)


def _compat_components3(
    runtime: Runtime,
    args: tuple[object, ...],
    name: str,
) -> tuple[ScalarInput, ScalarInput, ScalarInput]:
    if not args:
        values: tuple[object, ...] = ()
    elif len(args) == 1:
        value = args[0]
        if isinstance(value, (Point3, Vector3)):
            require_same_runtime(runtime, value)
            values = (value.x, value.y, value.z)
        elif isinstance(value, TopoDS_Vertex):
            point = vertex_point(value)
            values = (point.X(), point.Y(), point.Z())
        elif isinstance(value, (gp_Pnt, gp_Dir, gp_Vec, gp_XYZ)):
            values = (value.X(), value.Y(), value.Z())
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            values = tuple(value)
        else:
            values = (value,)
    else:
        values = args
    if len(values) > 3:
        raise TypeError(f"{name} expects at most three coordinates")
    padded = values + (0,) * (3 - len(values))
    return (
        cast(ScalarInput, padded[0]),
        cast(ScalarInput, padded[1]),
        cast(ScalarInput, padded[2]),
    )


def _sample_fractions(n: int, endpoint: bool) -> tuple[float, ...]:
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("sample count must be int")
    if n < 0:
        raise ValueError("sample count must be non-negative")
    if not isinstance(endpoint, bool):
        raise TypeError("endpoint must be bool")
    if n == 0:
        return ()
    if n == 1:
        return (0.0,)
    divisor = n - 1 if endpoint else n
    return tuple(index / divisor for index in range(n))


def _sample_scalar_range(
    runtime: Runtime,
    bounds: tuple[ScalarInput, ScalarInput],
    fractions: tuple[float, ...],
    name: str,
) -> list[Scalar]:
    if not isinstance(bounds, tuple) or len(bounds) != 2:
        raise TypeError(f"{name} must contain two scalar bounds")
    start = _as_scalar(runtime, bounds[0])
    delta = _as_scalar(runtime, bounds[1]) - start
    return [start + delta * fraction for fraction in fractions]


def _require_positive_number(value: Number, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be int or float")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return result


def _require_positive_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _require_int_between(
    value: int,
    name: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def _require_points(
    runtime: Runtime,
    points: Sequence[Point3],
    *,
    minimum: int,
    name: str,
) -> tuple[Point3, ...]:
    if isinstance(points, (str, bytes)) or not isinstance(points, Sequence):
        raise TypeError(f"{name} expects a sequence of Point3")
    values = tuple(points)
    if len(values) < minimum:
        raise ValueError(f"{name} requires at least {minimum} points")
    if not all(isinstance(point, Point3) for point in values):
        raise TypeError(f"{name} expects only Point3 values")
    for point in values:
        require_same_runtime(runtime, point)
    return values
