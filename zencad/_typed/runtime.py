"""Experimental typed ZenCad domain handles.

This module is intentionally private.  It is the vertical slice used to prove
that a stable domain API can contain an evalcache expression graph without
exposing lazy proxy types to callers.
"""

from __future__ import annotations

from collections.abc import Sequence
import math
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, TypeVar, cast, overload

from OCP.TopoDS import TopoDS_Shape, TopoDS_Vertex
from OCP.Geom import Geom_CartesianPoint
from OCP.Poly import Poly_Triangulation
from OCP.gp import gp_Dir, gp_Pnt, gp_Quaternion, gp_Vec, gp_XYZ
from evalcache import (
    CachePolicy,
    CacheStore,
    EvaluationMode,
    Evaluator,
    Expression,
    MappingCacheStore,
    ProgressHook,
    ResultSpec,
)

from zencad.occ_compat import read_brep, vertex_point, write_brep
from zencad.operation import using_runtime

from . import _operations as ops
from . import bounds as bounds_api
from . import curve_constructors as curve_api
from . import face_constructors as face_api
from . import modeling as modeling_api
from . import surfaces as surface_api
from . import sweeps as sweep_api
from . import text as text_api
from . import transforms as transform_api
from ._core import State, require_same_runtime
from .bounds import BoundaryBox
from .curves import Curve, Curve2
from .exttrans import MultiTransform
from .meshes import MeshData
from .records import CurveProjection, Interval
from .surfaces import (
    Surface,
    SweepLocationLaw,
    SweepScaleLaw,
    SweepSectionLaw,
    SweepTrihedron,
)
from .sweeps import PipeTransition, PipeTrihedron
from .text import FontAspect
from .topology import (
    SHELL_SPEC,
    SOLID_SPEC,
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
from .transforms import AffineTransform, Quaternion, Transform
from .values import (
    Number,
    Point2,
    Point3,
    Scalar,
    ScalarInput,
    Vector2,
    Vector3,
)
from .solid import (
    box as solid_box,
    cone as solid_cone,
    cube as solid_cube,
    cylinder as solid_cylinder,
    halfspace as solid_halfspace,
    make_solid as solid_make_solid,
    sphere as solid_sphere,
    torus as solid_torus,
)
from .booleans import (
    difference as topology_difference,
    empty_shape as topology_empty_shape,
    intersect as topology_intersect,
    intersection as topology_intersection,
    nullshape as topology_nullshape,
    section as topology_section,
    union as topology_union,
)

if TYPE_CHECKING:
    from .wire_builder import WireBuilder


ResolvedT = TypeVar("ResolvedT")
ShapeValueT = TypeVar("ShapeValueT", bound=Shape)

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
    "PipeTransition",
    "PipeTrihedron",
    "Runtime",
    "Shape",
    "Shell",
    "Solid",
    "Surface",
    "SweepLocationLaw",
    "SweepScaleLaw",
    "SweepSectionLaw",
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
        with using_runtime(self):
            return solid_box(x, y, z, center, size)

    def cube(
        self,
        x: ScalarInput | Vector3 | Sequence[ScalarInput] = 0,
        y: ScalarInput | None = None,
        z: ScalarInput | None = None,
        center: bool | str | None = None,
        size: ScalarInput | Vector3 | Sequence[ScalarInput] | None = None,
    ) -> Solid:
        """Compatibility alias for :meth:`box` with the legacy signature."""
        with using_runtime(self):
            return solid_cube(x, y, z, center, size)

    def sphere(
        self,
        r: ScalarInput,
        yaw: ScalarInput | None = None,
        pitch: ScalarInput | Sequence[ScalarInput] | None = None,
    ) -> Solid:
        with using_runtime(self):
            return solid_sphere(r, yaw, pitch)

    def cylinder(
        self,
        r: ScalarInput,
        h: ScalarInput,
        yaw: ScalarInput | None = None,
        center: bool = False,
    ) -> Solid:
        with using_runtime(self):
            return solid_cylinder(r, h, yaw, center)

    def cone(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        h: ScalarInput,
        yaw: ScalarInput | None = None,
        center: bool = False,
    ) -> Solid:
        with using_runtime(self):
            return solid_cone(r1, r2, h, yaw, center)

    def torus(
        self,
        r1: ScalarInput,
        r2: ScalarInput,
        yaw: ScalarInput | None = None,
        pitch: ScalarInput | Sequence[ScalarInput] | None = None,
    ) -> Solid:
        with using_runtime(self):
            return solid_torus(r1, r2, yaw, pitch)

    def halfspace(self) -> Solid:
        with using_runtime(self):
            return solid_halfspace()

    def make_solid(self, shells: Shell | Sequence[Shell], /) -> Solid:
        with using_runtime(self):
            return solid_make_solid(shells)

    def empty_shape(self) -> Shape:
        """Return the algebraic zero of topology without materializing it."""
        with using_runtime(self):
            return topology_empty_shape()

    def nullshape(self) -> Shape:
        """Legacy spelling for :meth:`empty_shape`."""
        with using_runtime(self):
            return topology_nullshape()

    def union(
        self,
        shapes: Shape | Sequence[Shape],
        /,
        *others: Shape,
    ) -> Shape:
        with using_runtime(self):
            return topology_union(shapes, *others)

    def intersect(
        self,
        shapes: Shape | Sequence[Shape],
        /,
        *others: Shape,
    ) -> Shape:
        with using_runtime(self):
            return topology_intersect(shapes, *others)

    def intersection(
        self,
        shapes: Shape | Sequence[Shape],
        /,
        *others: Shape,
    ) -> Shape:
        """Descriptive alias for the legacy :meth:`intersect` spelling."""
        with using_runtime(self):
            return topology_intersection(shapes, *others)

    def difference(
        self,
        shapes: Shape | Sequence[Shape],
        /,
        *others: Shape,
    ) -> Shape:
        with using_runtime(self):
            return topology_difference(shapes, *others)

    def section(
        self,
        left: Shape | ScalarInput | Point3 | Vector3 | Sequence[ScalarInput],
        right: Shape | ScalarInput | Point3 | Vector3 | Sequence[ScalarInput] = 0,
        /,
        *,
        pretty: bool = False,
    ) -> Shape:
        """Intersect shape boundaries, accepting legacy plane operands."""
        with using_runtime(self):
            return topology_section(left, right, pretty=pretty)

    def extrude(
        self,
        shape: Shape,
        vec: Vector3 | Sequence[ScalarInput] | ScalarInput,
        center: bool = False,
    ) -> Shape:
        with using_runtime(self):
            return sweep_api.extrude(shape, vec, center)

    def linear_extrude(
        self,
        shape: Shape,
        vec: Vector3 | Sequence[ScalarInput] | ScalarInput,
        center: bool = False,
    ) -> Shape:
        """Compatibility spelling for :meth:`extrude`."""
        with using_runtime(self):
            return sweep_api.linear_extrude(shape, vec, center)

    def revol(
        self,
        shape: Shape,
        r: ScalarInput | None = None,
        yaw: ScalarInput = 0,
    ) -> Shape:
        with using_runtime(self):
            return sweep_api.revol(shape, r, yaw)

    @overload
    def loft(
        self,
        sections: Sequence[Edge | Wire],
        smooth: bool = False,
        shell: Literal[False] = False,
        max_degree: int = 4,
    ) -> Solid: ...

    @overload
    def loft(
        self,
        sections: Sequence[Edge | Wire],
        smooth: bool = False,
        *,
        shell: Literal[True],
        max_degree: int = 4,
    ) -> Shell: ...

    @overload
    def loft(
        self,
        sections: Sequence[Edge | Wire],
        smooth: bool,
        shell: Literal[True],
        max_degree: int = 4,
    ) -> Shell: ...

    @overload
    def loft(
        self,
        sections: Sequence[Edge | Wire],
        smooth: bool = False,
        shell: bool = False,
        max_degree: int = 4,
    ) -> Solid | Shell: ...

    def loft(
        self,
        sections: Sequence[Edge | Wire],
        smooth: bool = False,
        shell: bool = False,
        max_degree: int = 4,
    ) -> Solid | Shell:
        with using_runtime(self):
            return sweep_api.loft(sections, smooth, shell, max_degree)

    def pipe(
        self,
        profile: Shape,
        spine: Edge | Wire,
        /,
        *,
        trihedron: PipeTrihedron = PipeTrihedron.CORRECTED_FRENET,
        force_approx_c1: bool = False,
    ) -> Shape:
        with using_runtime(self):
            return sweep_api.pipe(
                profile,
                spine,
                trihedron=trihedron,
                force_approx_c1=force_approx_c1,
            )

    @overload
    def pipe_shell(
        self,
        profiles: Sequence[Edge | Wire],
        spine: Edge | Wire,
        /,
        *,
        frenet: bool = False,
        approx_c1: bool = False,
        binormal: Vector3 | None = None,
        parallel: Vector3 | None = None,
        discrete: bool = False,
        solid: Literal[True] = True,
        transition: PipeTransition = PipeTransition.TRANSFORMED,
    ) -> Solid: ...

    @overload
    def pipe_shell(
        self,
        profiles: Sequence[Edge | Wire],
        spine: Edge | Wire,
        /,
        *,
        frenet: bool = False,
        approx_c1: bool = False,
        binormal: Vector3 | None = None,
        parallel: Vector3 | None = None,
        discrete: bool = False,
        solid: Literal[False],
        transition: PipeTransition = PipeTransition.TRANSFORMED,
    ) -> Shell: ...

    @overload
    def pipe_shell(
        self,
        profiles: Sequence[Edge | Wire],
        spine: Edge | Wire,
        /,
        *,
        frenet: bool = False,
        approx_c1: bool = False,
        binormal: Vector3 | None = None,
        parallel: Vector3 | None = None,
        discrete: bool = False,
        solid: bool = True,
        transition: PipeTransition = PipeTransition.TRANSFORMED,
    ) -> Solid | Shell: ...

    def pipe_shell(
        self,
        profiles: Sequence[Edge | Wire],
        spine: Edge | Wire,
        /,
        *,
        frenet: bool = False,
        approx_c1: bool = False,
        binormal: Vector3 | None = None,
        parallel: Vector3 | None = None,
        discrete: bool = False,
        solid: bool = True,
        transition: PipeTransition = PipeTransition.TRANSFORMED,
    ) -> Solid | Shell:
        with using_runtime(self):
            return sweep_api.pipe_shell(
                profiles,
                spine,
                frenet=frenet,
                approx_c1=approx_c1,
                binormal=binormal,
                parallel=parallel,
                discrete=discrete,
                solid=solid,
                transition=transition,
            )

    def sweep(
        self,
        profile: Edge | Wire,
        path: Edge | Wire,
        /,
        *,
        frenet: bool = False,
    ) -> Solid:
        """Compatibility spelling for a single-profile solid pipe shell."""
        with using_runtime(self):
            return sweep_api.sweep(profile, path, frenet=frenet)

    def revol2(
        self,
        profile: Shape,
        radius: ScalarInput,
        /,
        *,
        sections: int = 30,
        yaw: Interval | Sequence[ScalarInput] = (0, 2 * math.pi),
        roll: Interval | Sequence[ScalarInput] = (0, 0),
        parts: int | None = None,
    ) -> Solid:
        """Approximate a rolled revolution through discrete profile sections."""
        with using_runtime(self):
            return sweep_api.revol2(
                profile,
                radius,
                sections=sections,
                yaw=yaw,
                roll=roll,
                parts=parts,
            )

    def fillet(
        self,
        shape: Shape,
        radius: ScalarInput,
        references: Sequence[Point3] | None = None,
        /,
    ) -> Shape:
        with using_runtime(self):
            return modeling_api.fillet(shape, radius, references)

    def chamfer(
        self,
        shape: Shape,
        radius: ScalarInput,
        references: Sequence[Point3] | None = None,
        /,
    ) -> Shape:
        with using_runtime(self):
            return modeling_api.chamfer(shape, radius, references)

    def fillet2d(
        self,
        shape: Face,
        radius: ScalarInput,
        references: Sequence[Point3] | None = None,
        /,
    ) -> Face:
        with using_runtime(self):
            return modeling_api.fillet2d(shape, radius, references)

    @overload
    def restore_shapetype(self, shape: Solid, /) -> Solid: ...

    @overload
    def restore_shapetype(self, shape: Shell, /) -> Shell: ...

    @overload
    def restore_shapetype(self, shape: Face, /) -> Face: ...

    @overload
    def restore_shapetype(self, shape: Wire, /) -> Wire: ...

    @overload
    def restore_shapetype(self, shape: Edge, /) -> Edge: ...

    @overload
    def restore_shapetype(self, shape: Shape, /) -> Shape: ...

    def restore_shapetype(self, shape: Shape, /) -> Shape:
        with using_runtime(self):
            return modeling_api.restore_shapetype(shape)

    def triangulate(self, shape: Shape, deflection: Number, /) -> MeshData:
        _require_shape(self, shape, "triangulate")
        return shape.to_mesh(linear_deflection=deflection)

    def triangulate_face(self, shape: Face, deflection: Number, /) -> MeshData:
        if not isinstance(shape, Face):
            raise TypeError("triangulate_face expects Face")
        require_same_runtime(self, shape)
        return shape.triangulate(linear_deflection=deflection)

    def get_nodes(
        self,
        triangulation: MeshData | Poly_Triangulation,
        /,
    ) -> tuple[tuple[float, float, float], ...]:
        if isinstance(triangulation, MeshData):
            require_same_runtime(self, triangulation)
            return triangulation.get_nodes()
        if not isinstance(triangulation, Poly_Triangulation):
            raise TypeError("get_nodes expects MeshData or Poly_Triangulation")
        return tuple(
            (
                float(triangulation.Node(index).X()),
                float(triangulation.Node(index).Y()),
                float(triangulation.Node(index).Z()),
            )
            for index in range(1, triangulation.NbNodes() + 1)
        )

    def get_triangles(
        self,
        triangulation: MeshData | Poly_Triangulation,
        /,
    ) -> tuple[tuple[int, int, int], ...]:
        if isinstance(triangulation, MeshData):
            require_same_runtime(self, triangulation)
            return triangulation.get_triangles()
        if not isinstance(triangulation, Poly_Triangulation):
            raise TypeError("get_triangles expects MeshData or Poly_Triangulation")
        return tuple(
            tuple(value - 1 for value in triangulation.Triangle(index).Get())
            for index in range(1, triangulation.NbTriangles() + 1)
        )

    def mesh_to_poly_triangulation(
        self,
        mesh: MeshData,
        /,
    ) -> Poly_Triangulation:
        if not isinstance(mesh, MeshData):
            raise TypeError("mesh_to_poly_triangulation expects MeshData")
        require_same_runtime(self, mesh)
        return mesh.mesh_to_poly_triangulation()

    def to_brep(self, shape: Shape, path: str | PathLike[str], /) -> None:
        """Materialize and write a typed Shape at an explicit file boundary."""
        _require_shape(self, shape, "to_brep")
        resolved_path = str(Path(path).expanduser())
        if not write_brep(shape.native(), resolved_path):
            raise OSError(f"Failed to write BREP file: {resolved_path}")

    def from_brep(self, path: str | PathLike[str], /) -> Shape:
        """Read a BREP snapshot without retaining mutable native ownership."""
        resolved_path = str(Path(path).expanduser())
        native = TopoDS_Shape()
        if not read_brep(native, resolved_path):
            raise OSError(f"Failed to read BREP file: {resolved_path}")
        return Shape.from_ocp(native, runtime=self)

    def to_stl(
        self,
        shape: Shape,
        path: str | PathLike[str],
        deflection: Number,
        /,
    ) -> bool:
        """Write STL from an isolated native snapshot of a typed Shape."""
        from zencad.convert.api import _to_stl
        from zencad.geom.shape import Shape as ResolvedShape

        _require_shape(self, shape, "to_stl")
        if (
            isinstance(deflection, bool)
            or not isinstance(deflection, (int, float))
            or not math.isfinite(deflection)
            or deflection <= 0
        ):
            raise ValueError("to_stl deflection must be finite and positive")
        resolved_path = str(Path(path).expanduser())
        return bool(
            _to_stl(
                ResolvedShape(shape.native()),
                resolved_path,
                float(deflection),
            )
        )

    def to_svg_string(
        self,
        shape: Shape,
        color: object = (0, 0, 0),
        mapping: bool = False,
    ) -> str:
        from zencad.convert.svg import shape_to_svg_string
        from zencad.geom.shape import Shape as ResolvedShape

        _require_shape(self, shape, "to_svg_string")
        _require_bool(mapping, "to_svg_string mapping")
        return str(
            shape_to_svg_string(
                ResolvedShape(shape.native()),
                color,
                mapping,
            )
        )

    def to_svg(
        self,
        shape: Shape,
        path: str | PathLike[str],
        color: object = (0, 0, 0),
        mapping: bool = False,
    ) -> None:
        resolved_path = Path(path).expanduser()
        resolved_path.write_text(
            self.to_svg_string(shape, color, mapping),
            encoding="utf-8",
        )

    def from_svg_string(self, value: str, /) -> Shape:
        import evalcache

        from zencad.convert.svg import SvgReader
        from zencad.geom.shape import Shape as ResolvedShape

        if not isinstance(value, str):
            raise TypeError("from_svg_string expects str")
        legacy = evalcache.unlazy_if_need(SvgReader().read_string(value))
        if not isinstance(legacy, ResolvedShape):
            raise ValueError("SVG import did not produce a Shape")
        return Shape.from_ocp(legacy.Shape(), runtime=self)

    def from_svg(self, path: str | PathLike[str], /) -> Shape:
        resolved_path = Path(path).expanduser()
        return self.from_svg_string(resolved_path.read_text(encoding="utf-8"))

    @overload
    def sew(
        self,
        shapes: Sequence[Edge | Wire],
        sort: bool = True,
        /,
    ) -> Wire: ...

    @overload
    def sew(
        self,
        shapes: Sequence[Face | Shell],
        sort: bool = True,
        /,
    ) -> Shell: ...

    def sew(
        self,
        shapes: Sequence[Edge | Wire] | Sequence[Face | Shell],
        sort: bool = True,
        /,
    ) -> Wire | Shell:
        with using_runtime(self):
            return modeling_api.sew(shapes, sort)

    def offset(self, shape: Shape, distance: ScalarInput, /) -> Shape:
        with using_runtime(self):
            return modeling_api.offset(shape, distance)

    def thicksolid(
        self,
        shape: Solid,
        thickness: ScalarInput,
        references: Sequence[Point3],
        /,
    ) -> Solid:
        with using_runtime(self):
            return modeling_api.thicksolid(shape, thickness, references)

    def shapefix_solid(self, shape: Solid, /) -> Solid:
        with using_runtime(self):
            return modeling_api.shapefix_solid(shape)

    def unify(self, shape: ShapeValueT, /) -> ShapeValueT:
        with using_runtime(self):
            return cast(ShapeValueT, modeling_api.unify(shape))

    def near_vertex(self, shape: Shape, point: Point3, /) -> Vertex:
        with using_runtime(self):
            return modeling_api.near_vertex(shape, point)

    def near_edge(self, shape: Shape, point: Point3, /) -> Edge:
        with using_runtime(self):
            return modeling_api.near_edge(shape, point)

    def near_wire(self, shape: Shape, point: Point3, /) -> Wire:
        with using_runtime(self):
            return modeling_api.near_wire(shape, point)

    def near_face(self, shape: Shape, point: Point3, /) -> Face:
        with using_runtime(self):
            return modeling_api.near_face(shape, point)

    def near_shell(self, shape: Shape, point: Point3, /) -> Shell:
        with using_runtime(self):
            return modeling_api.near_shell(shape, point)

    def near_solid(self, shape: Shape, point: Point3, /) -> Solid:
        with using_runtime(self):
            return modeling_api.near_solid(shape, point)

    def near_compsolid(self, shape: Shape, point: Point3, /) -> CompSolid:
        with using_runtime(self):
            return modeling_api.near_compsolid(shape, point)

    def near_compound(self, shape: Shape, point: Point3, /) -> Compound:
        with using_runtime(self):
            return modeling_api.near_compound(shape, point)

    def project_point_on_curve(
        self,
        point: Point3,
        target: Curve | Edge,
        /,
    ) -> CurveProjection:
        with using_runtime(self):
            return modeling_api.project_point_on_curve(point, target)

    def project(self, point: Point3, target: Curve | Edge, /) -> CurveProjection:
        with using_runtime(self):
            return modeling_api.project(point, target)

    def empty_boundary_box(self) -> BoundaryBox:
        """Return the identity value for boundary-box union."""
        with using_runtime(self):
            return bounds_api.empty_boundary_box()

    def boundary_box(self, minimum: Point3, maximum: Point3, /) -> BoundaryBox:
        """Create a graph-preserving box from its opposite corner points."""
        with using_runtime(self):
            return bounds_api.boundary_box(minimum, maximum)

    def line(self, origin: Point3, direction: Vector3, /) -> Curve:
        with using_runtime(self):
            return curve_api.line(origin, direction)

    def circle_curve(self, radius: ScalarInput, /) -> Curve:
        with using_runtime(self):
            return curve_api.circle_curve(radius)

    def ellipse_curve(
        self,
        major_radius: ScalarInput,
        minor_radius: ScalarInput,
        /,
    ) -> Curve:
        with using_runtime(self):
            return curve_api.ellipse_curve(major_radius, minor_radius)

    def interpolate_curve(
        self,
        pnts: Sequence[Point3],
        tangs: Sequence[Vector3 | None] | None = None,
        closed: bool = False,
    ) -> Curve:
        with using_runtime(self):
            return curve_api.interpolate_curve(pnts, tangs, closed)

    def interpolate(
        self,
        pnts: Sequence[Point3],
        tangs: Sequence[Vector3 | None] | None = None,
        closed: bool = False,
    ) -> Edge:
        with using_runtime(self):
            return curve_api.interpolate(pnts, tangs, closed)

    def bezier_curve(
        self,
        poles: Sequence[Point3],
        weights: Sequence[ScalarInput] | None = None,
    ) -> Curve:
        with using_runtime(self):
            return curve_api.bezier_curve(poles, weights)

    def bezier(
        self,
        pnts: Sequence[Point3],
        weights: Sequence[ScalarInput] | None = None,
    ) -> Edge:
        with using_runtime(self):
            return curve_api.bezier(pnts, weights)

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
        with using_runtime(self):
            return curve_api.bspline_curve(
                poles,
                knots,
                muls,
                degree,
                periodic,
                weights,
                check_rational,
            )

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
        with using_runtime(self):
            return curve_api.bspline(
                poles,
                knots,
                muls,
                degree,
                periodic,
                weights,
                check_rational,
            )

    def make_edge(
        self,
        curve: Curve,
        interval: Interval | Sequence[ScalarInput] | None = None,
        /,
    ) -> Edge:
        with using_runtime(self):
            return curve_api.make_edge(curve, interval)

    def circle_arc(self, p1: Point3, p2: Point3, p3: Point3, /) -> Edge:
        with using_runtime(self):
            return curve_api.circle_arc(p1, p2, p3)

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
        with using_runtime(self):
            return curve_api._svg_elliptic_arc(
                start,
                end,
                radius_x,
                radius_y,
                x_axis_angle,
                large,
                sweep,
            )

    def make_wire(
        self,
        *shapes: Edge | Wire | Sequence[Edge | Wire],
    ) -> Wire:
        with using_runtime(self):
            return curve_api.make_wire(*shapes)

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
        with using_runtime(self):
            return curve_api.rounded_polysegment(pnts, r, closed)

    def helix(
        self,
        r: ScalarInput,
        h: ScalarInput,
        step: ScalarInput | None = None,
        pitch: ScalarInput | None = None,
        angle: ScalarInput = 0,
        left: bool = False,
    ) -> Wire:
        with using_runtime(self):
            return curve_api.helix(r, h, step, pitch, angle, left)

    def segment2(self, start: Point2, end: Point2, /) -> Curve2:
        with using_runtime(self):
            return curve_api.segment2(start, end)

    def ellipse2(
        self,
        major_radius: ScalarInput,
        minor_radius: ScalarInput,
        /,
    ) -> Curve2:
        with using_runtime(self):
            return curve_api.ellipse2(major_radius, minor_radius)

    def trim_curve2(
        self,
        curve: Curve2,
        start: ScalarInput,
        end: ScalarInput,
        /,
    ) -> Curve2:
        with using_runtime(self):
            return curve_api.trim_curve2(curve, start, end)

    def cylinder_surface(self, radius: ScalarInput, /) -> Surface:
        with using_runtime(self):
            return surface_api.cylinder_surface(radius)

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
        with using_runtime(self):
            return surface_api.sweep_surface(
                section,
                spine,
                scale=scale,
                trihedron=trihedron,
                tolerance=tolerance,
                continuity=continuity,
                max_degree=max_degree,
                max_segments=max_segments,
            )

    def constant_sweep_scale(
        self,
        scale: ScalarInput,
        domain: Interval,
        /,
    ) -> SweepScaleLaw:
        """Describe a constant sweep scale over an explicit domain."""
        with using_runtime(self):
            return surface_api.constant_sweep_scale(scale, domain)

    def evolved_sweep_section(
        self,
        section: Curve,
        scale: SweepScaleLaw,
        /,
    ) -> SweepSectionLaw:
        """Describe a curve section evolved by a scale law."""
        with using_runtime(self):
            return surface_api.evolved_sweep_section(section, scale)

    def sweep_location(
        self,
        spine: Curve,
        trihedron: SweepTrihedron = SweepTrihedron.CORRECTED_FRENET,
        /,
    ) -> SweepLocationLaw:
        """Describe a spine location using an explicit trihedron law."""
        with using_runtime(self):
            return surface_api.sweep_location(spine, trihedron)

    def sweep_surface_from_laws(
        self,
        section: SweepSectionLaw,
        location: SweepLocationLaw,
        /,
        *,
        tolerance: Number = 1e-6,
        continuity: int = 2,
        max_degree: int = 5,
        max_segments: int = 20,
    ) -> Surface:
        """Build a surface from immutable section and location laws."""
        with using_runtime(self):
            return surface_api.sweep_surface_from_laws(
                section,
                location,
                tolerance=tolerance,
                continuity=continuity,
                max_degree=max_degree,
                max_segments=max_segments,
            )

    def segment(self, start: Point3, end: Point3, /) -> Edge:
        with using_runtime(self):
            return curve_api.segment(start, end)

    def polysegment(
        self,
        points: Sequence[Point3],
        /,
        *,
        closed: bool = False,
    ) -> Wire:
        with using_runtime(self):
            return curve_api.polysegment(points, closed=closed)

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
        with using_runtime(self):
            return face_api.polygon(points, wire)

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
        with using_runtime(self):
            return face_api.rectangle(a, b, center, wire)

    def rectangle_wire(
        self,
        a: ScalarInput,
        b: ScalarInput,
        center: bool = False,
    ) -> Wire:
        with using_runtime(self):
            return face_api.rectangle_wire(a, b, center)

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
        with using_runtime(self):
            return face_api.square(a, b, center, wire)

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
        with using_runtime(self):
            return face_api.ngon(r, n, wire)

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
        with using_runtime(self):
            return face_api.circle(r, angle, wire)

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
        with using_runtime(self):
            return face_api.ellipse(r1, r2, angle, wire)

    def fill(self, shapes: Edge | Wire | Sequence[Edge | Wire], /) -> Face:
        with using_runtime(self):
            return face_api.fill(shapes)

    def interpolate2(
        self,
        refs: Sequence[Sequence[Point3]],
        degmin: int = 3,
        degmax: int = 7,
    ) -> Face:
        with using_runtime(self):
            return face_api.interpolate2(refs, degmin, degmax)

    def fix_face(self, shape: Face, /) -> Face:
        with using_runtime(self):
            return face_api.fix_face(shape)

    def infplane(self) -> Face:
        with using_runtime(self):
            return face_api.infplane()

    def ruled(self, first: Edge, second: Edge, /) -> Face:
        with using_runtime(self):
            return face_api.ruled(first, second)

    def widewire(
        self,
        spine: Edge | Wire,
        r: ScalarInput,
        circled_joints: bool = True,
        circled_ends: bool = True,
    ) -> Shape:
        with using_runtime(self):
            return face_api.widewire(spine, r, circled_joints, circled_ends)

    def register_font(
        self,
        font_path: str | PathLike[str],
        aspect: FontAspect = FontAspect.UNDEFINED,
    ) -> None:
        return text_api.register_font(font_path, aspect)

    def text_to_brep(
        self,
        text: str,
        font_name: str,
        size: ScalarInput,
        aspect: FontAspect = FontAspect.REGULAR,
        composite_curve: bool = False,
    ) -> Compound:
        with using_runtime(self):
            return text_api.text_to_brep(
                text,
                font_name,
                size,
                aspect,
                composite_curve,
            )

    def textshape(
        self,
        text: str,
        fontname: str,
        size: ScalarInput,
        composite_curve: bool = False,
    ) -> Compound:
        with using_runtime(self):
            return text_api.textshape(text, fontname, size, composite_curve)

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
        with using_runtime(self):
            return transform_api.quaternion(x, y, z, w)

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
        with using_runtime(self):
            return transform_api.quaternion_axis_angle(axis, angle)

    def identity_transform(self) -> Transform:
        with using_runtime(self):
            return transform_api.identity_transform()

    def identity_affine_transform(self) -> AffineTransform:
        with using_runtime(self):
            return transform_api.identity_affine_transform()

    def affine_transform(
        self,
        rows: Sequence[Sequence[ScalarInput]],
        /,
    ) -> AffineTransform:
        with using_runtime(self):
            return transform_api.affine_transform(rows)

    def affine(
        self,
        rows: Sequence[Sequence[ScalarInput]],
        /,
    ) -> AffineTransform:
        with using_runtime(self):
            return transform_api.affine(rows)

    def nulltrans(self) -> Transform:
        with using_runtime(self):
            return transform_api.identity_transform()

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
        with using_runtime(self):
            if len(args) == 1 and isinstance(args[0], Vector3):
                return transform_api.translation(args[0])
            if len(args) == 3:
                return transform_api.move(*args)
            raise TypeError("translation expects Vector3 or three scalar coordinates")

    def move(self, *args: object) -> Transform:
        with using_runtime(self):
            return transform_api.move(*args)

    def translate(self, *args: object) -> Transform:
        with using_runtime(self):
            return transform_api.move(*args)

    def moveX(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveX(value)

    def moveY(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveY(value)

    def moveZ(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveZ(value)

    def movX(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveX(value)

    def movY(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveY(value)

    def movZ(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveZ(value)

    def translateX(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveX(value)

    def translateY(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveY(value)

    def translateZ(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveZ(value)

    def right(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.moveX(value)

    def left(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.left(value)

    def forw(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.forw(value)

    def back(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.back(value)

    def up(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.up(value)

    def down(self, value: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.down(value)

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
        with using_runtime(self):
            if len(args) == 1 and isinstance(args[0], Quaternion):
                return transform_api.rotation(args[0])
            if len(args) == 2 and isinstance(args[0], Vector3):
                return transform_api.rotate(args[0], cast(ScalarInput, args[1]))
            raise TypeError("rotation expects Quaternion or Vector3 and angle")

    def rotate(
        self,
        axis: Vector3 | Sequence[ScalarInput],
        angle: ScalarInput | None = None,
        /,
    ) -> Transform:
        with using_runtime(self):
            return transform_api.rotate(axis, angle)

    def rotate_quat(
        self,
        quaternion: Quaternion | gp_Quaternion | Sequence[ScalarInput],
        /,
    ) -> Transform:
        with using_runtime(self):
            return transform_api.rotate_quat(quaternion)

    def rotateX(self, angle: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.rotateX(angle)

    def rotateY(self, angle: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.rotateY(angle)

    def rotateZ(self, angle: ScalarInput, /) -> Transform:
        with using_runtime(self):
            return transform_api.rotateZ(angle)

    def scale(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> Transform:
        with using_runtime(self):
            return transform_api.scale(factor, center=center)

    def scaleXYZ(
        self,
        x: ScalarInput,
        y: ScalarInput,
        z: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> AffineTransform:
        with using_runtime(self):
            return transform_api.scaleXYZ(x, y, z, center=center)

    def scaleX(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> AffineTransform:
        with using_runtime(self):
            return transform_api.scaleX(factor, center=center)

    def scaleY(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> AffineTransform:
        with using_runtime(self):
            return transform_api.scaleY(factor, center=center)

    def scaleZ(
        self,
        factor: ScalarInput,
        /,
        *,
        center: Point3 | None = None,
    ) -> AffineTransform:
        with using_runtime(self):
            return transform_api.scaleZ(factor, center=center)

    def mirror(
        self,
        normal: Vector3,
        /,
        *,
        origin: Point3 | None = None,
    ) -> Transform:
        with using_runtime(self):
            return transform_api.mirror(normal, origin=origin)

    def mirror_plane(self, *normal: object) -> Transform:
        with using_runtime(self):
            return transform_api.mirror_plane(*normal)

    def mirrorXY(self) -> Transform:
        with using_runtime(self):
            return transform_api.mirrorXY()

    def mirrorYZ(self) -> Transform:
        with using_runtime(self):
            return transform_api.mirrorYZ()

    def mirrorXZ(self) -> Transform:
        with using_runtime(self):
            return transform_api.mirrorXZ()

    def mirror_axis(self, *axis: object) -> Transform:
        with using_runtime(self):
            return transform_api.mirror_axis(*axis)

    def mirrorX(self) -> Transform:
        with using_runtime(self):
            return transform_api.mirrorX()

    def mirrorY(self) -> Transform:
        with using_runtime(self):
            return transform_api.mirrorY()

    def mirrorZ(self) -> Transform:
        with using_runtime(self):
            return transform_api.mirrorZ()

    def mirrorO(self, *origin: object) -> Transform:
        with using_runtime(self):
            return transform_api.mirrorO(*origin)

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
        with using_runtime(self):
            return transform_api.short_rotate(source, target)


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")


def _require_shape(runtime: Runtime, shape: Shape, name: str) -> None:
    if not isinstance(shape, Shape):
        raise TypeError(f"{name} expects Shape")
    require_same_runtime(runtime, shape)


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
