import json
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore
from OCP.BRep import BRep_Builder
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import (
    TopoDS_Compound,
    TopoDS_Edge,
    TopoDS_Shell,
    TopoDS_Solid,
    TopoDS_Vertex,
)
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec

import zencad
from zencad import geom as typed
from zencad._native.shape import Shape as ResolvedShape
from zencad._native.validation import ShapeValidationError
from zencad.occ_compat import as_face
from zencad.runtime.scene_protocol import encode_brep


def _open_shell() -> TopoDS_Shell:
    builder = BRep_Builder()
    shell = TopoDS_Shell()
    builder.MakeShell(shell)
    box = BRepPrimAPI_MakeBox(2, 2, 2).Solid()
    explorer = TopExp_Explorer(box, TopAbs_FACE)
    builder.Add(shell, as_face(explorer.Current()))
    return shell


def _open_solid() -> TopoDS_Solid:
    builder = BRep_Builder()
    solid = TopoDS_Solid()
    builder.MakeSolid(solid)
    builder.Add(solid, _open_shell())
    return solid


def _curve_less_edge() -> TopoDS_Edge:
    builder = BRep_Builder()
    edge = TopoDS_Edge()
    builder.MakeEdge(edge)
    for x in (0.0, 1.0):
        vertex = TopoDS_Vertex()
        builder.MakeVertex(vertex, gp_Pnt(x, 0, 0), 1e-7)
        builder.Add(edge, vertex)
    return edge


class ShapeValidationTest(unittest.TestCase):
    def test_reports_are_structured_json_ready_and_context_aware(self):
        self.assertTrue(zencad.box(2).validate().valid)
        self.assertTrue(ResolvedShape(_open_shell()).validate().valid)

        invalid = ResolvedShape(_open_solid())
        report = invalid.validate(exact=True, parallel=True)
        payload = report.to_dict()

        self.assertFalse(report.valid)
        self.assertEqual(report.shape_type, "solid")
        self.assertEqual(report.issues[0].code, "not_closed")
        self.assertEqual(report.issues[0].path, "solid/shell[0]")
        self.assertEqual(report.issues[0].context_path, "solid")
        self.assertTrue(payload["exact"])
        self.assertTrue(payload["parallel"])
        json.dumps(payload)

        with self.assertRaises(ShapeValidationError) as raised:
            invalid.assert_valid()
        self.assertIs(raised.exception.report.__class__, report.__class__)
        valid = zencad.box(1)
        self.assertIs(valid.assert_valid(), valid)

    def test_degenerate_topology_and_compound_paths_are_reported(self):
        edge_report = ResolvedShape(_curve_less_edge()).validate()
        self.assertFalse(edge_report.valid)
        self.assertIn("no_3d_curve", {issue.code for issue in edge_report.issues})

        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)
        builder.Add(compound, BRepPrimAPI_MakeBox(1, 1, 1).Solid())
        builder.Add(compound, _open_solid())
        report = ResolvedShape(compound).validate()

        self.assertFalse(report.valid)
        self.assertTrue(
            any(issue.path.startswith("compound/solid[1]") for issue in report.issues)
        )

    def test_shared_topology_keeps_first_path_and_distinguishes_locations(self):
        # A box's shared edges/vertices are counted once across all six faces.
        box = ResolvedShape(BRepPrimAPI_MakeBox(1, 1, 1).Solid())
        self.assertEqual(box.validate().checked_subshapes, 34)

        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)
        solid = _open_solid()
        translation = gp_Trsf()
        translation.SetTranslation(gp_Vec(5, 0, 0))
        builder.Add(compound, solid)
        builder.Add(compound, solid.Reversed())
        builder.Add(compound, solid.Moved(TopLoc_Location(translation)))

        report = ResolvedShape(compound).validate()
        self.assertFalse(report.valid)
        self.assertEqual(
            report.checked_subshapes,
            1 + 2 * ResolvedShape(solid).validate().checked_subshapes,
        )
        self.assertEqual(
            [(issue.code, issue.path, issue.context_path) for issue in report.issues],
            [
                ("not_closed", "compound/solid[0]/shell[0]", "compound/solid[0]"),
                ("not_closed", "compound/solid[2]/shell[0]", "compound/solid[2]"),
            ],
        )

    def test_large_topology_and_many_error_contexts_finish_promptly(self):
        # Bound the whole subprocess so a quadratic traversal cannot stall CI.
        # The allowance includes interpreter startup on slower platforms.
        process = subprocess.run(
            [sys.executable, "-c", textwrap.dedent("""
                from utest.shape_validation_test import (
                    BRep_Builder, BRepPrimAPI_MakeBox, TopoDS_Compound,
                    TopLoc_Location, gp_Trsf, gp_Vec, ResolvedShape, _open_solid,
                )

                builder = BRep_Builder()
                compound = TopoDS_Compound()
                builder.MakeCompound(compound)
                box = BRepPrimAPI_MakeBox(1, 1, 1).Solid()
                broken = _open_solid()
                for source in (box, broken):
                    for i in range(1000):
                        transform = gp_Trsf()
                        transform.SetTranslation(gp_Vec(3 * i, 0, 0))
                        builder.Add(compound, source.Moved(TopLoc_Location(transform)))
                    report = ResolvedShape(compound).validate()
                    if source is box:
                        assert report.valid and report.checked_subshapes == 34001
                    else:
                        assert not report.valid
                        assert len(report.issues) == 1000
                        for i, issue in enumerate(report.issues, start=1000):
                            assert issue.code == "not_closed"
                            assert issue.path == f"compound/solid[{i}]/shell[0]"
                            assert issue.context_path == f"compound/solid[{i}]"
            """)],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_clean_and_heal_preserve_the_source_and_return_owned_shapes(self):
        source = zencad.box(1) + zencad.box(1).translate(1, 0, 0)
        source_value = source.native()
        before = encode_brep(source_value)

        cleaned = source.clean()
        healed = source.heal()

        self.assertEqual(encode_brep(source_value), before)
        self.assertFalse(cleaned.native().IsSame(source_value))
        self.assertFalse(healed.native().IsSame(source_value))
        self.assertEqual(len(source.faces()), 10)
        self.assertEqual(len(cleaned.faces()), 6)
        self.assertAlmostEqual(float(cleaned.mass()), float(source.mass()))


class TypedShapeValidationTest(unittest.TestCase):
    def test_typed_api_materializes_reports_and_preserves_handle_types(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    solid = context.call(typed.box, 2)

                    report = context.call(typed.validate, solid)
                    self.assertTrue(report.valid)
                    self.assertTrue(solid.is_valid())
                    self.assertIs(context.call(typed.assert_valid, solid), solid)
                    self.assertIs(type(context.call(typed.clean, solid)), typed.Solid)
                    self.assertIs(type(solid.heal()), typed.Solid)

    def test_typed_invalid_shape_raises_with_the_same_report_contract(self):
        context = typed.Context.deferred(cache=False)
        invalid = typed.Solid.from_ocp(_open_solid(), context=context)

        report = typed.validate(invalid)
        self.assertFalse(report.valid)
        self.assertEqual(report.issues[0].code, "not_closed")
        with self.assertRaises(typed.ShapeValidationError) as raised:
            invalid.assert_valid()
        self.assertEqual(raised.exception.report.to_dict(), report.to_dict())


if __name__ == "__main__":
    unittest.main()
