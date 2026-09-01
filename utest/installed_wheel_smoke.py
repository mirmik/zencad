"""Smoke the installed wheel from a directory outside the source checkout."""

import importlib.metadata
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import evalcache
import evalcache.v2
from evalcache.dircache_v2 import DirCache_v2

import zencad
from zencad import _typed as typed
from zencad.convert.api import _from_brep, _to_brep, _to_stl
from zencad.operation import DomainOperation, using_runtime
from zencad.runtime import RunnerMessage, RunnerSupervisor
from zencad.runtime.scene_protocol import decode_mesh
from zencad.scene_draft import SceneDraft


def main():
    assert evalcache.Expression is evalcache.v2.Expression
    assert evalcache.LazyObject is not None
    assert RunnerMessage is not None
    assert RunnerSupervisor is not None
    assert zencad.__version__ == importlib.metadata.version("zencad")
    checkout = os.environ.get("GITHUB_WORKSPACE")
    if checkout:
        package_path = Path(zencad.__file__).resolve()
        assert not package_path.is_relative_to(Path(checkout).resolve())

    installed = {
        distribution.metadata["Name"].lower()
        for distribution in importlib.metadata.distributions()
    }
    assert not installed.intersection({"vtk", "pyqt5", "zenframe", "termin"})

    with TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        zencad.lazy.cache = DirCache_v2(str(temporary_path / "cache"))

        shape = zencad.box(20, center=True) - zencad.sphere(5)
        expected_mass = shape.unlazy().mass()
        brep_path = temporary_path / "smoke.brep"
        stl_path = temporary_path / "smoke.stl"

        _to_brep(shape.unlazy(), str(brep_path))
        restored = _from_brep(str(brep_path))
        assert abs(restored.mass() - expected_mass) < 1e-8
        assert _to_stl(shape.unlazy(), str(stl_path), 0.1)
        assert stl_path.stat().st_size > 0

        typed_runtime = typed.Runtime.deferred(cache=False)
        assert isinstance(typed.circle_curve, DomainOperation)
        assert isinstance(typed.make_wire, DomainOperation)
        assert isinstance(typed.cylinder_surface, DomainOperation)
        assert isinstance(typed.sweep_surface_from_laws, DomainOperation)
        assert isinstance(typed.extrude, DomainOperation)
        assert isinstance(typed.revol, DomainOperation)
        assert isinstance(typed.loft, DomainOperation)
        assert isinstance(typed.pipe, DomainOperation)
        assert isinstance(typed.pipe_shell, DomainOperation)
        assert isinstance(typed.revol2, DomainOperation)
        assert isinstance(typed.boundary_box, DomainOperation)
        assert isinstance(typed.empty_boundary_box, DomainOperation)
        assert isinstance(typed.boundbox, DomainOperation)
        assert isinstance(typed.fillet, DomainOperation)
        assert isinstance(typed.offset, DomainOperation)
        assert isinstance(typed.unify, DomainOperation)
        assert isinstance(typed.near_face, DomainOperation)
        assert isinstance(typed.circle, DomainOperation)
        assert isinstance(typed.ellipse, DomainOperation)
        assert isinstance(typed.fill, DomainOperation)
        assert isinstance(typed.interpolate2, DomainOperation)
        assert isinstance(typed.fix_face, DomainOperation)
        assert isinstance(typed.infplane, DomainOperation)
        assert isinstance(typed.ruled, DomainOperation)
        assert isinstance(typed.widewire, DomainOperation)
        assert isinstance(typed.text_to_brep, DomainOperation)
        with using_runtime(typed_runtime):
            module_curve = typed.circle_curve(2)
            module_segment = typed.segment(
                typed_runtime.point3(0, 0, 0),
                typed_runtime.point3(1, 0, 0),
            )
            module_wire = typed.make_wire(module_segment)
            module_face = typed.rectangle(2, 1)
            module_circle = typed.circle(2)
            module_filled = typed.fill(typed.rectangle_wire(2, 1))
        assert type(module_curve) is typed.Curve
        assert type(module_wire) is typed.Wire
        assert type(module_face) is typed.Face
        assert type(module_circle) is typed.Face
        assert type(module_filled) is typed.Face
        curve = typed_runtime.circle_curve(2)
        curve2 = typed_runtime.segment2(
            typed_runtime.point2(0, 0),
            typed_runtime.point2(3, 0),
        ).trim(0.5, 2.5)
        assert type(curve) is typed.Curve
        assert curve.point(0).value() == (2.0, 0.0, 0.0)
        assert type(curve2) is typed.Curve2
        assert curve2.point(0.5).value() == (0.5, 0.0)
        rotated_curve2 = curve2.rotate(0.5)
        assert type(rotated_curve2) is typed.Curve2
        surface = typed_runtime.cylinder_surface(2)
        sweep_surface = typed_runtime.sweep_surface(
            typed_runtime.circle_curve(1),
            typed_runtime.circle_curve(3),
        )
        assert type(surface) is typed.Surface
        assert surface.point(0, 3).value() == (2.0, 0.0, 3.0)
        assert type(surface.u_range()) is typed.Interval
        mapped_edge = surface.map(
            typed_runtime.segment2(
                typed_runtime.point2(0, 0),
                typed_runtime.point2(1, 2),
            )
        )
        assert type(mapped_edge) is typed.Edge
        assert len(mapped_edge.endpoints()) == 2
        assert type(sweep_surface) is typed.Surface
        assert len(sweep_surface.native().Bounds()) == 4
        sweep_spine = typed_runtime.circle_curve(3)
        scale_law = typed_runtime.constant_sweep_scale(1, sweep_spine.range())
        section_law = typed_runtime.evolved_sweep_section(
            typed_runtime.circle_curve(1),
            scale_law,
        )
        location_law = typed_runtime.sweep_location(sweep_spine)
        assert type(scale_law) is typed.SweepScaleLaw
        assert type(section_law) is typed.SweepSectionLaw
        assert type(location_law) is typed.SweepLocationLaw
        assert type(
            typed_runtime.sweep_surface_from_laws(section_law, location_law)
        ) is typed.Surface
        with using_runtime(typed_runtime):
            module_surface = typed.cylinder_surface(2)
            module_surface_sweep = typed.sweep_surface_from_laws(
                section_law,
                location_law,
            )
        assert type(module_surface) is typed.Surface
        assert type(module_surface_sweep) is typed.Surface
        sweep_profile = typed_runtime.rectangle(1, 2, center=True)
        assert type(typed_runtime.extrude(sweep_profile, 4)) is typed.Shape
        assert type(typed_runtime.revol(sweep_profile, 3)) is typed.Shape
        loft_start = typed_runtime.rectangle_wire(1, 2, center=True)
        loft_end = typed_runtime.rectangle_wire(2, 1, center=True).up(3)
        assert type(typed_runtime.loft((loft_start, loft_end))) is typed.Solid
        pipe_profile = typed_runtime.circle(1, wire=True)
        pipe_spine = typed_runtime.segment(
            typed_runtime.point3(),
            typed_runtime.point3(0, 0, 5),
        )
        assert type(
            typed_runtime.pipe(
                pipe_profile,
                pipe_spine,
                trihedron=typed.PipeTrihedron.FRENET,
            )
        ) is typed.Shape
        assert type(
            typed_runtime.pipe_shell(
                (pipe_profile,),
                pipe_spine,
                transition=typed.PipeTransition.ROUND_CORNER,
            )
        ) is typed.Solid
        assert type(
            typed_runtime.revol2(
                sweep_profile,
                3,
                sections=8,
                yaw=(0, math.pi),
                roll=(0, math.pi / 2),
            )
        ) is typed.Solid
        with using_runtime(typed_runtime):
            module_sweeps = (
                typed.extrude(sweep_profile, 4),
                typed.revol(sweep_profile, 3),
                typed.loft((loft_start, loft_end)),
                typed.pipe(pipe_profile, pipe_spine),
                typed.pipe_shell((pipe_profile,), pipe_spine),
                typed.revol2(sweep_profile, 3, sections=8),
            )
        assert tuple(type(value) for value in module_sweeps) == (
            typed.Shape,
            typed.Shape,
            typed.Solid,
            typed.Shape,
            typed.Solid,
            typed.Solid,
        )
        bounds = typed_runtime.box(2, 3, 4).boundbox()
        assert type(bounds) is typed.BoundaryBox
        assert type(bounds.value()) is typed.BoundaryBoxRecord
        assert all(
            abs(actual - expected) < 1e-12
            for actual, expected in zip(bounds.center.value(), (1.0, 1.5, 2.0))
        )
        with using_runtime(typed_runtime):
            module_bounds = typed.boundbox(typed_runtime.box(2))
            explicit_bounds = typed.boundary_box(
                typed_runtime.point3(),
                typed_runtime.point3(1, 2, 3),
            )
        assert type(module_bounds) is typed.BoundaryBox
        assert explicit_bounds.value().maximum == (1.0, 2.0, 3.0)
        mesh = typed_runtime.box(2).to_mesh()
        assert type(mesh) is typed.MeshData
        assert type(mesh.value()) is typed.MeshDataRecord
        assert mesh.vertex_count == 24
        assert mesh.triangle_count == 12
        assert type(typed_runtime.rectangle(2, 3).triangulate()) is typed.MeshData
        assert decode_mesh(mesh.display_payload()).triangles == list(mesh.triangles)
        boolean_left = typed_runtime.box(2)
        boolean_right = typed_runtime.box(2).translate(1, 0, 0)
        assert abs(typed_runtime.union(boolean_left, boolean_right).mass() - 12) < 1e-8
        assert abs(typed_runtime.intersect((boolean_left, boolean_right)).mass() - 4) < 1e-8
        assert len(typed_runtime.section(boolean_left, 1).edges()) > 0
        nearest_face = typed_runtime.near_face(
            boolean_left,
            typed_runtime.point3(0.5, 0.5, 3),
        )
        assert type(nearest_face) is typed.Face
        projection = typed_runtime.project(
            typed_runtime.point3(1, 2, 0),
            typed_runtime.segment(
                typed_runtime.point3(0, 0, 0),
                typed_runtime.point3(3, 0, 0),
            ),
        )
        assert type(projection) is typed.CurveProjection
        assert projection.value() == ((1.0, 0.0, 0.0), 1.0, 2.0)
        assert type(typed_runtime.unify(boolean_left)) is typed.Solid
        assert type(typed_runtime.offset(boolean_left, 0.1)) is typed.Shape
        with using_runtime(typed_runtime):
            module_modeling = (
                typed.fillet(boolean_left, 0.1),
                typed.offset(boolean_left, 0.1),
                typed.unify(boolean_left),
                typed.near_face(
                    boolean_left,
                    typed_runtime.point3(0.5, 0.5, 3),
                ),
            )
            module_projection = typed.project(
                typed_runtime.point3(1, 2, 0),
                typed_runtime.segment(
                    typed_runtime.point3(),
                    typed_runtime.point3(3, 0, 0),
                ),
            )
        assert tuple(type(value) for value in module_modeling) == (
            typed.Shape,
            typed.Shape,
            typed.Solid,
            typed.Face,
        )
        assert module_projection.value() == ((1.0, 0.0, 0.0), 1.0, 2.0)
        draft = SceneDraft(generation=1)
        draft.add(boolean_left)
        draft.add(mesh, display_mode="shaded")
        draft.add(typed_runtime.point3(1, 2, 3))
        typed_snapshot = draft.snapshot()
        assert tuple(item.kind for item in typed_snapshot.objects) == (
            "brep",
            "mesh",
            "point",
        )
        edge_curve = typed_runtime.box(2).edges()[0].curve()
        face_surface = typed_runtime.box(2).faces()[0].surface()
        assert type(edge_curve) is typed.Curve
        assert edge_curve.range().value() == (0.0, 2.0)
        assert type(face_surface) is typed.Surface
        assert face_surface.u_range().length().value() == 2.0
        circle_face = typed_runtime.circle(3)
        ellipse_edge = typed_runtime.ellipse(4, 2, wire=True)
        polygon_wire = typed_runtime.rectangle(4, 3, wire=True)
        holed_face = typed_runtime.fill(
            (polygon_wire, typed_runtime.rectangle(2, 1, wire=True))
        )
        assert type(circle_face) is typed.Face
        assert type(ellipse_edge) is typed.Edge
        assert type(polygon_wire) is typed.Wire
        assert type(holed_face) is typed.Face
        assert len(holed_face.edges()) == 8
        wide_shape = typed_runtime.widewire(
            typed_runtime.segment(
                typed_runtime.point3(0, 0, 0),
                typed_runtime.point3(10, 0, 0),
            ),
            1,
        )
        assert type(wide_shape) is typed.Shape
        assert (
            abs(wide_shape.SurfaceProperties().mass.value() - (20 + 3.141592653589793))
            < 1e-8
        )
        shell = typed_runtime.make_shell(circle_face)
        tetrahedron = typed_runtime.tetrahedron()
        hexahedron_shell = typed_runtime.hexahedron(shell=True)
        assert type(shell) is typed.Shell
        assert type(tetrahedron) is typed.Solid
        assert type(hexahedron_shell) is typed.Shell
        assert len(tetrahedron.faces()) == 4
        assert len(hexahedron_shell.faces()) == 6
        font_path = (
            Path(zencad.__file__).resolve().parent
            / "examples"
            / "fonts"
            / "mandarinc.ttf"
        )
        typed_runtime.register_font(font_path)
        typed_text = typed_runtime.textshape("Hello", "MandarinC", 10)
        typed.register_font(font_path)
        with using_runtime(typed_runtime):
            module_text = typed.text_to_brep("Module", "MandarinC", 10)
        assert type(typed_text) is typed.Compound
        assert type(module_text) is typed.Compound
        assert len(typed_text.edges()) > 0
        assert len(module_text.edges()) > 0
        builder = (
            typed_runtime.wire_builder(defrel=True)
            .l(2, 0)
            .svg_circle_arc(2, 0, False, True, 0, 4)
            .l(-2, 0)
            .close()
        )
        built_wire = builder.build()
        assert type(builder) is typed.WireBuilder
        assert type(built_wire) is typed.Wire
        assert built_wire.is_closed()
        assert len(built_wire.edges()) == 4

        script_path = temporary_path / "headless_model.py"
        script_path.write_text(
            "import sys\n"
            "from zencad import box, display, show\n"
            "display(box(1))\n"
            "show()\n"
            "assert 'PyQt5' not in sys.modules\n"
            "assert 'zenframe' not in sys.modules\n",
            encoding="utf-8",
        )
        subprocess.run(
            [sys.executable, "-m", "zencad", "--no-show", str(script_path)],
            cwd=temporary_path,
            check=True,
        )
        console_script = shutil.which("zencad")
        assert console_script is not None
        subprocess.run(
            [console_script, "--no-show", str(script_path)],
            cwd=temporary_path,
            check=True,
        )

    print("Installed wheel geometry/I/O smoke: OK")


if __name__ == "__main__":
    main()
