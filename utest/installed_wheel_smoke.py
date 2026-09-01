"""Smoke the installed wheel from a directory outside the source checkout."""

import importlib.metadata
import io
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import evalcache
import evalcache.v2

import zencad
from zencad import _typed as typed
from zencad.operation import DomainOperation, using_context
from zencad.runtime import RunnerMessage, RunnerSupervisor
from zencad.runtime.scene_protocol import decode_mesh
from zencad.scene_draft import SceneDraft


def main():
    assert evalcache.Expression is evalcache.v2.Expression
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
        zencad.configure(cache_dir=temporary_path / "cache")

        shape = zencad.box(20, center=True) - zencad.sphere(5)
        expected_mass = shape.mass().value()
        brep_path = temporary_path / "smoke.brep"
        stl_path = temporary_path / "smoke.stl"

        zencad.to_brep(shape, brep_path)
        restored = zencad.from_brep(brep_path)
        assert abs(restored.mass().value() - expected_mass) < 1e-8
        assert zencad.to_stl(shape, stl_path, 0.1)
        assert stl_path.stat().st_size > 0

        assert "Context" in typed.__all__
        assert zencad.Context is typed.Context
        assert not hasattr(typed.Context, "box")
        assert not hasattr(typed, "RuntimeCompatibility")
        assert not hasattr(zencad, "Runtime")
        assert not hasattr(zencad, "lazy")
        typed_context = typed.Context.deferred(cache=False)
        with typed.using_context(typed_context):
            context_shape = typed.box(2).translate(1, 2, 3)
            context_wire = (
                typed.WireBuilder(context=typed_context).l(1, 0).l(0, 1).build()
            )
        assert type(context_shape) is typed.Solid
        assert context_shape.context is typed_context
        assert context_wire.context is typed_context
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
        assert isinstance(typed.to_mesh, DomainOperation)
        assert isinstance(typed.mesh_boundbox, DomainOperation)
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
        assert isinstance(typed.make_shell, DomainOperation)
        assert isinstance(typed.fill3d, DomainOperation)
        assert isinstance(typed.polyhedron_shell, DomainOperation)
        assert isinstance(typed.convex_hull_shape, DomainOperation)
        assert isinstance(typed.split, DomainOperation)
        assert isinstance(typed.slice, DomainOperation)
        assert isinstance(typed.draft, DomainOperation)
        assert typed.ShapeList is typed.DeferredSequence
        assert typed.Axis.Z.direction == (0.0, 0.0, 1.0)
        assert typed.Plane.XY.normal == (0.0, 0.0, 1.0)
        parts = zencad.split(
            zencad.box(2),
            zencad.infplane().up(1),
        )
        assert len(parts) == 2
        assert [round(float(part.mass()), 6) for part in parts] == [4.0, 4.0]
        with typed.using_context(typed_context):
            typed_body = typed.box(2)
            typed_parts = typed.slice(typed_body, z=1)
        assert isinstance(typed_parts, typed.SliceResult)
        assert round(float(typed_parts.lower.mass()), 6) == 4.0
        assert round(float(typed_parts.upper.mass()), 6) == 4.0
        with typed.using_context(typed_context):
            draft_body = typed.box(2)
            drafted = typed.draft(draft_body, draft_body.faces()[0], 0.05)
        assert type(drafted) is typed.Solid
        assert drafted.context is typed_context
        assert float(drafted.mass()) > 0
        selected_edges = draft_body.edges().filter_by(typed.Axis.Z)
        selected_faces = draft_body.faces().normal_to(typed.Axis.X)
        assert type(selected_edges) is typed.ShapeList
        assert len(selected_edges) > 0
        assert len(selected_faces) == 2
        selected_fillet = typed.fillet(draft_body, 0.1, selected_edges)
        selected_draft = typed.draft(draft_body, selected_faces, 0.05)
        assert float(selected_fillet.mass()) > 0
        assert float(selected_draft.mass()) > 0
        with using_context(typed_context):
            module_curve = typed.circle_curve(2)
            module_segment = typed.segment(
                typed_context.call(typed.point3, 0, 0, 0),
                typed_context.call(typed.point3, 1, 0, 0),
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
        curve = typed_context.call(typed.circle_curve, 2)
        curve2 = typed_context.call(
            typed.segment2,
            typed_context.call(typed.point2, 0, 0),
            typed_context.call(typed.point2, 3, 0),
        ).trim(0.5, 2.5)
        assert type(curve) is typed.Curve
        assert curve.point(0).value() == (2.0, 0.0, 0.0)
        assert type(curve2) is typed.Curve2
        assert curve2.point(0.5).value() == (0.5, 0.0)
        rotated_curve2 = curve2.rotate(0.5)
        assert type(rotated_curve2) is typed.Curve2
        surface = typed_context.call(typed.cylinder_surface, 2)
        sweep_surface = typed_context.call(
            typed.sweep_surface,
            typed_context.call(typed.circle_curve, 1),
            typed_context.call(typed.circle_curve, 3),
        )
        assert type(surface) is typed.Surface
        assert surface.point(0, 3).value() == (2.0, 0.0, 3.0)
        assert type(surface.u_range()) is typed.Interval
        mapped_edge = surface.map(
            typed_context.call(
                typed.segment2,
                typed_context.call(typed.point2, 0, 0),
                typed_context.call(typed.point2, 1, 2),
            )
        )
        assert type(mapped_edge) is typed.Edge
        assert len(mapped_edge.endpoints()) == 2
        assert type(sweep_surface) is typed.Surface
        assert len(sweep_surface.native().Bounds()) == 4
        sweep_spine = typed_context.call(typed.circle_curve, 3)
        scale_law = typed_context.call(
            typed.constant_sweep_scale, 1, sweep_spine.range()
        )
        section_law = typed_context.call(
            typed.evolved_sweep_section,
            typed_context.call(typed.circle_curve, 1),
            scale_law,
        )
        location_law = typed_context.call(typed.sweep_location, sweep_spine)
        assert type(scale_law) is typed.SweepScaleLaw
        assert type(section_law) is typed.SweepSectionLaw
        assert type(location_law) is typed.SweepLocationLaw
        assert (
            type(
                typed_context.call(
                    typed.sweep_surface_from_laws, section_law, location_law
                )
            )
            is typed.Surface
        )
        with using_context(typed_context):
            module_surface = typed.cylinder_surface(2)
            module_surface_sweep = typed.sweep_surface_from_laws(
                section_law,
                location_law,
            )
        assert type(module_surface) is typed.Surface
        assert type(module_surface_sweep) is typed.Surface
        sweep_profile = typed_context.call(typed.rectangle, 1, 2, center=True)
        assert type(typed_context.call(typed.extrude, sweep_profile, 4)) is typed.Shape
        assert type(typed_context.call(typed.revol, sweep_profile, 3)) is typed.Shape
        loft_start = typed_context.call(typed.rectangle_wire, 1, 2, center=True)
        loft_end = typed_context.call(typed.rectangle_wire, 2, 1, center=True).up(3)
        assert (
            type(typed_context.call(typed.loft, (loft_start, loft_end))) is typed.Solid
        )
        pipe_profile = typed_context.call(typed.circle, 1, wire=True)
        pipe_spine = typed_context.call(
            typed.segment,
            typed_context.call(
                typed.point3,
            ),
            typed_context.call(typed.point3, 0, 0, 5),
        )
        assert (
            type(
                typed_context.call(
                    typed.pipe,
                    pipe_profile,
                    pipe_spine,
                    trihedron=typed.PipeTrihedron.FRENET,
                )
            )
            is typed.Shape
        )
        assert (
            type(
                typed_context.call(
                    typed.pipe_shell,
                    (pipe_profile,),
                    pipe_spine,
                    transition=typed.PipeTransition.ROUND_CORNER,
                )
            )
            is typed.Solid
        )
        assert (
            type(
                typed_context.call(
                    typed.revol2,
                    sweep_profile,
                    3,
                    sections=8,
                    yaw=(0, math.pi),
                    roll=(0, math.pi / 2),
                )
            )
            is typed.Solid
        )
        with using_context(typed_context):
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
        bounds = typed_context.call(typed.box, 2, 3, 4).boundbox()
        assert type(bounds) is typed.BoundaryBox
        assert type(bounds.value()) is typed.BoundaryBoxRecord
        assert all(
            abs(actual - expected) < 1e-12
            for actual, expected in zip(bounds.center.value(), (1.0, 1.5, 2.0))
        )
        with using_context(typed_context):
            module_bounds = typed.boundbox(typed_context.call(typed.box, 2))
            explicit_bounds = typed.boundary_box(
                typed_context.call(
                    typed.point3,
                ),
                typed_context.call(typed.point3, 1, 2, 3),
            )
        assert type(module_bounds) is typed.BoundaryBox
        assert explicit_bounds.value().maximum == (1.0, 2.0, 3.0)
        mesh = typed_context.call(typed.box, 2).to_mesh()
        assert type(mesh) is typed.MeshData
        assert type(mesh.value()) is typed.MeshDataRecord
        assert mesh.vertex_count == 24
        assert mesh.triangle_count == 12
        assert (
            type(typed_context.call(typed.rectangle, 2, 3).triangulate())
            is typed.MeshData
        )
        with using_context(typed_context):
            module_mesh = typed.to_mesh(typed_context.call(typed.box, 2))
            module_face_mesh = typed.triangulate(
                typed_context.call(typed.rectangle, 2, 3)
            )
        assert type(module_mesh) is typed.MeshData
        assert type(module_face_mesh) is typed.MeshData
        assert (
            typed.mesh_boundbox(module_mesh).value() == module_mesh.boundbox().value()
        )
        assert typed.get_nodes(module_mesh) == module_mesh.positions
        assert typed.get_triangles(module_mesh) == module_mesh.triangles
        native_mesh = typed.mesh_to_poly_triangulation(module_mesh)
        assert typed.get_nodes(native_mesh) == module_mesh.positions
        assert typed.get_triangles(native_mesh) == module_mesh.triangles
        assert typed.mesh_display_payload(module_mesh) == module_mesh.display_payload()
        typed_brep_path = temporary_path / "typed-module.brep"
        typed_stl_path = temporary_path / "typed-module.stl"
        typed_svg_path = temporary_path / "typed-module.svg"
        typed.to_brep(typed_context.call(typed.box, 2), typed_brep_path)
        assert typed.to_stl(typed_context.call(typed.box, 2), typed_stl_path, 0.1)
        typed_svg = typed.to_svg_string(typed_context.call(typed.rectangle, 2, 3))
        typed.to_svg(typed_context.call(typed.rectangle, 2, 3), typed_svg_path)
        with using_context(typed_context):
            assert type(typed.from_brep(typed_brep_path)) is typed.Shape
            assert type(typed.from_svg_string(typed_svg)) is typed.Shape
            assert type(typed.from_svg(typed_svg_path)) is typed.Shape
        assert decode_mesh(mesh.display_payload()).triangles == list(mesh.triangles)
        boolean_left = typed_context.call(typed.box, 2)
        boolean_right = typed_context.call(typed.box, 2).translate(1, 0, 0)
        assert (
            abs(
                typed_context.call(typed.union, boolean_left, boolean_right).mass() - 12
            )
            < 1e-8
        )
        assert (
            abs(
                typed_context.call(
                    typed.intersect, (boolean_left, boolean_right)
                ).mass()
                - 4
            )
            < 1e-8
        )
        assert len(typed_context.call(typed.section, boolean_left, 1).edges()) > 0
        nearest_face = typed_context.call(
            typed.near_face,
            boolean_left,
            typed_context.call(typed.point3, 0.5, 0.5, 3),
        )
        assert type(nearest_face) is typed.Face
        projection = typed_context.call(
            typed.project,
            typed_context.call(typed.point3, 1, 2, 0),
            typed_context.call(
                typed.segment,
                typed_context.call(typed.point3, 0, 0, 0),
                typed_context.call(typed.point3, 3, 0, 0),
            ),
        )
        assert type(projection) is typed.CurveProjection
        assert projection.value() == ((1.0, 0.0, 0.0), 1.0, 2.0)
        assert type(typed_context.call(typed.unify, boolean_left)) is typed.Solid
        assert (
            typed_context.call(typed.validate, boolean_left).to_dict()["valid"] is True
        )
        assert typed_context.call(typed.is_valid, boolean_left)
        assert typed_context.call(typed.assert_valid, boolean_left) is boolean_left
        assert type(typed_context.call(typed.clean, boolean_left)) is typed.Solid
        assert type(typed_context.call(typed.heal, boolean_left)) is typed.Solid
        assert zencad.box(1).validate().valid
        assert zencad.box(1).assert_valid().is_valid()
        legacy_3mf = io.BytesIO()
        zencad.export_3mf(zencad.box(1), legacy_3mf, name="Wheel smoke")
        assert legacy_3mf.getvalue().startswith(b"PK")
        typed_step = io.BytesIO()
        typed_3mf = io.BytesIO()
        typed_context.call(typed.export_step, boolean_left, typed_step)
        typed_context.call(typed.export_3mf, boolean_left, typed_3mf)
        assert typed_step.getvalue().startswith(b"ISO-10303-21")
        assert typed_3mf.getvalue().startswith(b"PK")
        assert type(typed_context.call(typed.offset, boolean_left, 0.1)) is typed.Shape
        with using_context(typed_context):
            module_modeling = (
                typed.fillet(boolean_left, 0.1),
                typed.offset(boolean_left, 0.1),
                typed.unify(boolean_left),
                typed.near_face(
                    boolean_left,
                    typed_context.call(typed.point3, 0.5, 0.5, 3),
                ),
            )
            module_projection = typed.project(
                typed_context.call(typed.point3, 1, 2, 0),
                typed_context.call(
                    typed.segment,
                    typed_context.call(
                        typed.point3,
                    ),
                    typed_context.call(typed.point3, 3, 0, 0),
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
        draft.add(typed_context.call(typed.point3, 1, 2, 3))
        typed_snapshot = draft.snapshot()
        assert tuple(item.kind for item in typed_snapshot.objects) == (
            "brep",
            "mesh",
            "point",
        )
        edge_curve = typed_context.call(typed.box, 2).edges()[0].curve()
        face_surface = typed_context.call(typed.box, 2).faces()[0].surface()
        assert type(edge_curve) is typed.Curve
        assert edge_curve.range().value() == (0.0, 2.0)
        assert type(face_surface) is typed.Surface
        assert face_surface.u_range().length().value() == 2.0
        circle_face = typed_context.call(typed.circle, 3)
        ellipse_edge = typed_context.call(typed.ellipse, 4, 2, wire=True)
        polygon_wire = typed_context.call(typed.rectangle, 4, 3, wire=True)
        holed_face = typed_context.call(
            typed.fill,
            (polygon_wire, typed_context.call(typed.rectangle, 2, 1, wire=True)),
        )
        assert type(circle_face) is typed.Face
        assert type(ellipse_edge) is typed.Edge
        assert type(polygon_wire) is typed.Wire
        assert type(holed_face) is typed.Face
        assert len(holed_face.edges()) == 8
        wide_shape = typed_context.call(
            typed.widewire,
            typed_context.call(
                typed.segment,
                typed_context.call(typed.point3, 0, 0, 0),
                typed_context.call(typed.point3, 10, 0, 0),
            ),
            1,
        )
        assert type(wide_shape) is typed.Shape
        assert (
            abs(wide_shape.SurfaceProperties().mass.value() - (20 + 3.141592653589793))
            < 1e-8
        )
        shell = typed_context.call(typed.make_shell, circle_face)
        tetrahedron = typed_context.call(
            typed.tetrahedron,
        )
        hexahedron_shell = typed_context.call(typed.hexahedron, shell=True)
        with using_context(typed_context):
            module_shell = typed.make_shell(circle_face)
            module_tetrahedron = typed.tetrahedron()
        assert type(shell) is typed.Shell
        assert type(tetrahedron) is typed.Solid
        assert type(hexahedron_shell) is typed.Shell
        assert type(module_shell) is typed.Shell
        assert type(module_tetrahedron) is typed.Solid
        assert len(tetrahedron.faces()) == 4
        assert len(hexahedron_shell.faces()) == 6
        font_path = (
            Path(zencad.__file__).resolve().parent
            / "examples"
            / "fonts"
            / "mandarinc.ttf"
        )
        typed_context.call(typed.register_font, font_path)
        typed_text = typed_context.call(typed.textshape, "Hello", "MandarinC", 10)
        typed.register_font(font_path)
        with using_context(typed_context):
            module_text = typed.text_to_brep("Module", "MandarinC", 10)
        assert type(typed_text) is typed.Compound
        assert type(module_text) is typed.Compound
        assert len(typed_text.edges()) > 0
        assert len(module_text.edges()) > 0
        builder = (
            typed_context.call(typed.wire_builder, defrel=True)
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
