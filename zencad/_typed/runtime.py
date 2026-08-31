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
from . import _bound_operations as bound_ops
from . import _curve_operations as curve_ops
from . import _surface_operations as surface_ops
from . import _text_operations as text_ops
from . import _transform_operations as transform_ops
from ._core import State, require_same_runtime
from .bounds import BOUNDARY_BOX_SPEC, BoundaryBox
from .curves import CURVE2_SPEC, CURVE_SPEC, Curve, Curve2
from .exttrans import MultiTransform
from .meshes import MeshData
from .records import CurveProjection, Interval
from .surfaces import (
    SURFACE_SPEC,
    Surface,
    SweepLocationLaw,
    SweepScaleLaw,
    SweepSectionLaw,
    SweepTrihedron,
)
from .sweeps import PipeTransition, PipeTrihedron
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
    _angle_state,
    _optional_scalar_state,
    _scalar_state,
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
        _require_shape(self, shape, "extrude")
        return shape.extrude(vec, center)

    def linear_extrude(
        self,
        shape: Shape,
        vec: Vector3 | Sequence[ScalarInput] | ScalarInput,
        center: bool = False,
    ) -> Shape:
        """Compatibility spelling for :meth:`extrude`."""
        return self.extrude(shape, vec, center)

    def revol(
        self,
        shape: Shape,
        r: ScalarInput | None = None,
        yaw: ScalarInput = 0,
    ) -> Shape:
        _require_shape(self, shape, "revol")
        return shape.revol(r, yaw)

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
        _require_bool(smooth, "loft smooth")
        _require_bool(shell, "loft shell")
        resolved_degree = _require_positive_int(max_degree, "loft max_degree")
        values = _require_wire_parts(self, (sections,), "loft")
        if len(values) < 2:
            raise ValueError("loft requires at least two sections")
        result_spec = SHELL_SPEC if shell else SOLID_SPEC
        expression = self._expression(
            ops.loft_shapes,
            result=result_spec,
            args=(
                tuple(value._state for value in values),
                smooth,
                shell,
                resolved_degree,
            ),
            operation_id="zencad.typed.loft",
        )
        if shell:
            return Shell._from_state(self, expression)
        return Solid._from_state(self, expression)

    def pipe(
        self,
        profile: Shape,
        spine: Edge | Wire,
        /,
        *,
        trihedron: PipeTrihedron = PipeTrihedron.CORRECTED_FRENET,
        force_approx_c1: bool = False,
    ) -> Shape:
        _require_shape(self, profile, "pipe profile")
        _require_pipe_spine(self, spine, "pipe spine")
        if not isinstance(trihedron, PipeTrihedron):
            raise TypeError("pipe trihedron must be PipeTrihedron")
        _require_bool(force_approx_c1, "pipe force_approx_c1")
        expression = self._expression(
            ops.pipe_shape,
            result=SHAPE_SPEC,
            args=(
                profile._state,
                spine._state,
                trihedron.value,
                force_approx_c1,
            ),
            operation_id="zencad.typed.pipe",
        )
        return Shape._from_state(self, expression)

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
        values = _require_wire_parts(self, (profiles,), "pipe_shell profiles")
        _require_pipe_spine(self, spine, "pipe_shell spine")
        _require_bool(frenet, "pipe_shell frenet")
        _require_bool(approx_c1, "pipe_shell approx_c1")
        _require_bool(discrete, "pipe_shell discrete")
        _require_bool(solid, "pipe_shell solid")
        if not isinstance(transition, PipeTransition):
            raise TypeError("pipe_shell transition must be PipeTransition")
        for value, name in ((binormal, "binormal"), (parallel, "parallel")):
            if value is not None:
                if not isinstance(value, Vector3):
                    raise TypeError(f"pipe_shell {name} must be Vector3 or None")
                require_same_runtime(self, value)
        selected_modes = sum(
            (frenet, binormal is not None, parallel is not None, discrete)
        )
        if selected_modes > 1:
            raise ValueError("pipe_shell orientation modes are mutually exclusive")
        result_spec = SOLID_SPEC if solid else SHELL_SPEC
        expression = self._expression(
            ops.pipe_shell_shapes,
            result=result_spec,
            args=(
                tuple(value._state for value in values),
                spine._state,
                frenet,
                approx_c1,
                None if binormal is None else binormal._state,
                None if parallel is None else parallel._state,
                discrete,
                solid,
                transition.value,
            ),
            operation_id="zencad.typed.pipe_shell",
        )
        if solid:
            return Solid._from_state(self, expression)
        return Shell._from_state(self, expression)

    def sweep(
        self,
        profile: Edge | Wire,
        path: Edge | Wire,
        /,
        *,
        frenet: bool = False,
    ) -> Solid:
        """Compatibility spelling for a single-profile solid pipe shell."""
        return self.pipe_shell((profile,), path, frenet=frenet)

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
        _require_shape(self, profile, "revol2 profile")
        resolved_sections = _require_positive_int(sections, "revol2 sections")
        if resolved_sections < 2:
            raise ValueError("revol2 sections must be at least two")
        if parts is not None:
            resolved_parts = _require_positive_int(parts, "revol2 parts")
            if resolved_sections < resolved_parts * 2:
                raise ValueError(
                    "revol2 sections must provide at least two per part"
                )
        else:
            resolved_parts = None
        yaw_states = _interval_state(self, yaw, "revol2 yaw")
        roll_states = _interval_state(self, roll, "revol2 roll")
        assert yaw_states is not None and roll_states is not None
        expression = self._expression(
            ops.revolve_sections_shape,
            result=SOLID_SPEC,
            args=(
                profile._state,
                _scalar_state(self, radius),
                resolved_sections,
                yaw_states,
                roll_states,
                resolved_parts,
            ),
            operation_id="zencad.typed.revol2",
        )
        return Solid._from_state(self, expression)

    def fillet(
        self,
        shape: Shape,
        radius: ScalarInput,
        references: Sequence[Point3] | None = None,
        /,
    ) -> Shape:
        _require_shape(self, shape, "fillet")
        return shape.fillet(radius, references)

    def chamfer(
        self,
        shape: Shape,
        radius: ScalarInput,
        references: Sequence[Point3] | None = None,
        /,
    ) -> Shape:
        _require_shape(self, shape, "chamfer")
        return shape.chamfer(radius, references)

    def fillet2d(
        self,
        shape: Face,
        radius: ScalarInput,
        references: Sequence[Point3] | None = None,
        /,
    ) -> Face:
        if not isinstance(shape, Face):
            raise TypeError("fillet2d expects Face")
        require_same_runtime(self, shape)
        return shape.fillet2d(radius, references)

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
        _require_shape(self, shape, "restore_shapetype")
        candidates = (
            shape.solids(),
            shape.shells(),
            shape.faces(),
            shape.wires(),
            shape.edges(),
        )
        for candidates_of_kind in candidates:
            if len(candidates_of_kind) == 1:
                return candidates_of_kind[0]
        return shape

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
        _require_bool(sort, "sew sort")
        values = _require_sew_shapes(self, shapes)
        states = tuple(shape._state for shape in values)
        if all(isinstance(shape, (Edge, Wire)) for shape in values):
            expression = self._expression(
                ops.sew_wire,
                result=WIRE_SPEC,
                args=(states, sort),
                operation_id="zencad.typed.sew.wire",
            )
            return Wire._from_state(self, expression)
        expression = self._expression(
            ops.sew_shell,
            result=SHELL_SPEC,
            args=(states,),
            operation_id="zencad.typed.sew.shell",
        )
        return Shell._from_state(self, expression)

    def offset(self, shape: Shape, distance: ScalarInput, /) -> Shape:
        _require_shape(self, shape, "offset")
        return shape.offset(distance)

    def thicksolid(
        self,
        shape: Solid,
        thickness: ScalarInput,
        references: Sequence[Point3],
        /,
    ) -> Solid:
        if not isinstance(shape, Solid):
            raise TypeError("thicksolid expects Solid")
        require_same_runtime(self, shape)
        return shape.thicksolid(thickness, references)

    def shapefix_solid(self, shape: Solid, /) -> Solid:
        if not isinstance(shape, Solid):
            raise TypeError("shapefix_solid expects Solid")
        require_same_runtime(self, shape)
        return shape.shapefix_solid()

    def unify(self, shape: ShapeValueT, /) -> ShapeValueT:
        _require_shape(self, shape, "unify")
        return shape.unify()

    def near_vertex(self, shape: Shape, point: Point3, /) -> Vertex:
        _require_shape(self, shape, "near_vertex")
        return shape.near_vertex(point)

    def near_edge(self, shape: Shape, point: Point3, /) -> Edge:
        _require_shape(self, shape, "near_edge")
        return shape.near_edge(point)

    def near_wire(self, shape: Shape, point: Point3, /) -> Wire:
        _require_shape(self, shape, "near_wire")
        return shape.near_wire(point)

    def near_face(self, shape: Shape, point: Point3, /) -> Face:
        _require_shape(self, shape, "near_face")
        return shape.near_face(point)

    def near_shell(self, shape: Shape, point: Point3, /) -> Shell:
        _require_shape(self, shape, "near_shell")
        return shape.near_shell(point)

    def near_solid(self, shape: Shape, point: Point3, /) -> Solid:
        _require_shape(self, shape, "near_solid")
        return shape.near_solid(point)

    def near_compsolid(self, shape: Shape, point: Point3, /) -> CompSolid:
        _require_shape(self, shape, "near_compsolid")
        return shape.near_compsolid(point)

    def near_compound(self, shape: Shape, point: Point3, /) -> Compound:
        _require_shape(self, shape, "near_compound")
        return shape.near_compound(point)

    def project_point_on_curve(
        self,
        point: Point3,
        target: Curve | Edge,
        /,
    ) -> CurveProjection:
        if not isinstance(point, Point3):
            raise TypeError("project_point_on_curve point must be Point3")
        if not isinstance(target, (Curve, Edge)):
            raise TypeError("project_point_on_curve target must be Curve or Edge")
        require_same_runtime(self, point)
        require_same_runtime(self, target)
        curve = target.curve() if isinstance(target, Edge) else target
        parameter = curve.lower_distance_parameter(point)
        projected = curve.point(parameter)
        return CurveProjection(
            projected,
            parameter,
            (projected - point).length(),
        )

    def project(self, point: Point3, target: Curve | Edge, /) -> CurveProjection:
        return self.project_point_on_curve(point, target)

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
        scale_law = self.constant_sweep_scale(scale, spine.range())
        section_law = self.evolved_sweep_section(section, scale_law)
        location_law = self.sweep_location(spine, trihedron)
        return self.sweep_surface_from_laws(
            section_law,
            location_law,
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
        if not isinstance(domain, Interval):
            raise TypeError("constant_sweep_scale domain must be Interval")
        require_same_runtime(self, domain.lower)
        require_same_runtime(self, domain.upper)
        return SweepScaleLaw(
            Scalar._from_state(self, _scalar_state(self, scale)),
            domain,
        )

    def evolved_sweep_section(
        self,
        section: Curve,
        scale: SweepScaleLaw,
        /,
    ) -> SweepSectionLaw:
        """Describe a curve section evolved by a scale law."""
        if not isinstance(section, Curve):
            raise TypeError("evolved_sweep_section section must be Curve")
        if not isinstance(scale, SweepScaleLaw):
            raise TypeError("evolved_sweep_section scale must be SweepScaleLaw")
        require_same_runtime(self, section)
        if scale.runtime is not self:
            raise ValueError("cannot mix handles from different typed runtimes")
        return SweepSectionLaw(section, scale)

    def sweep_location(
        self,
        spine: Curve,
        trihedron: SweepTrihedron = SweepTrihedron.CORRECTED_FRENET,
        /,
    ) -> SweepLocationLaw:
        """Describe a spine location using an explicit trihedron law."""
        if not isinstance(spine, Curve):
            raise TypeError("sweep_location spine must be Curve")
        if not isinstance(trihedron, SweepTrihedron):
            raise TypeError("sweep_location trihedron must be SweepTrihedron")
        require_same_runtime(self, spine)
        return SweepLocationLaw(spine, trihedron)

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
        if not isinstance(section, SweepSectionLaw):
            raise TypeError("sweep_surface_from_laws section must be SweepSectionLaw")
        if not isinstance(location, SweepLocationLaw):
            raise TypeError(
                "sweep_surface_from_laws location must be SweepLocationLaw"
            )
        if section.runtime is not self or location.runtime is not self:
            raise ValueError("cannot mix handles from different typed runtimes")
        resolved_tolerance = _require_positive_number(
            tolerance,
            "sweep_surface_from_laws tolerance",
        )
        resolved_continuity = _require_int_between(
            continuity,
            "sweep_surface_from_laws continuity",
            minimum=0,
            maximum=3,
        )
        resolved_max_degree = _require_positive_int(
            max_degree,
            "sweep_surface_from_laws max_degree",
        )
        resolved_max_segments = _require_positive_int(
            max_segments,
            "sweep_surface_from_laws max_segments",
        )
        expression = self._expression(
            surface_ops.sweep_surface,
            result=SURFACE_SPEC,
            args=(
                section.section._state,
                section.scale.scale._state,
                section.scale.domain.lower._state,
                section.scale.domain.upper._state,
                location.spine._state,
                location.trihedron.value,
                resolved_tolerance,
                resolved_continuity,
                resolved_max_degree,
                resolved_max_segments,
            ),
            operation_id="zencad.typed.sweep_surface_from_laws",
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


def _require_shape(runtime: Runtime, shape: Shape, name: str) -> None:
    if not isinstance(shape, Shape):
        raise TypeError(f"{name} expects Shape")
    require_same_runtime(runtime, shape)


def _require_sew_shapes(
    runtime: Runtime,
    shapes: Sequence[Edge | Wire] | Sequence[Face | Shell],
) -> tuple[Edge | Wire | Face | Shell, ...]:
    if isinstance(shapes, (str, bytes)) or not isinstance(shapes, Sequence):
        raise TypeError("sew expects a sequence of topology handles")
    values = tuple(shapes)
    if not values:
        raise ValueError("sew requires at least one topology handle")
    wire_family = all(isinstance(shape, (Edge, Wire)) for shape in values)
    shell_family = all(isinstance(shape, (Face, Shell)) for shape in values)
    if not wire_family and not shell_family:
        raise TypeError("sew operands must all be Edge/Wire or all be Face/Shell")
    for shape in values:
        require_same_runtime(runtime, shape)
    return values


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


def _require_pipe_spine(
    runtime: Runtime,
    spine: Edge | Wire,
    name: str,
) -> None:
    if not isinstance(spine, (Edge, Wire)):
        raise TypeError(f"{name} must be Edge or Wire")
    require_same_runtime(runtime, spine)


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
