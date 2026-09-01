import json
import unittest

from evalcache.v2 import EvaluationMode, MemoryCacheStore
from OCP.BRep import BRep_Builder
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import (
    TopoDS_Compound,
    TopoDS_Edge,
    TopoDS_Shell,
    TopoDS_Solid,
    TopoDS_Vertex,
)
from OCP.gp import gp_Pnt

import zencad
from zencad import _typed as typed
from zencad.geom.shape import Shape as ResolvedShape
from zencad.geom.validation import ShapeValidationError
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


class LegacyShapeValidationTest(unittest.TestCase):
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
        valid = zencad.box(1).unlazy()
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

    def test_clean_and_heal_preserve_the_source_and_return_owned_shapes(self):
        source = zencad.box(1) + zencad.box(1).translate(1, 0, 0)
        source_value = source.unlazy()
        before = encode_brep(source_value)

        cleaned = source.clean().unlazy()
        healed = source.heal().unlazy()

        self.assertEqual(encode_brep(source_value), before)
        self.assertFalse(cleaned.Shape().IsSame(source_value.Shape()))
        self.assertFalse(healed.Shape().IsSame(source_value.Shape()))
        self.assertEqual(len(source.faces()), 10)
        self.assertEqual(len(cleaned.faces()), 6)
        self.assertAlmostEqual(cleaned.mass(), source.mass())


class TypedShapeValidationTest(unittest.TestCase):
    def test_typed_api_materializes_reports_and_preserves_handle_types(self):
        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    runtime = typed.Runtime(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    solid = runtime.box(2)

                    report = runtime.validate(solid)
                    self.assertTrue(report.valid)
                    self.assertTrue(solid.is_valid())
                    self.assertIs(runtime.assert_valid(solid), solid)
                    self.assertIs(type(runtime.clean(solid)), typed.Solid)
                    self.assertIs(type(solid.heal()), typed.Solid)

    def test_typed_invalid_shape_raises_with_the_same_report_contract(self):
        runtime = typed.Runtime.deferred(cache=False)
        invalid = typed.Solid.from_ocp(_open_solid(), runtime=runtime)

        report = typed.validate(invalid)
        self.assertFalse(report.valid)
        self.assertEqual(report.issues[0].code, "not_closed")
        with self.assertRaises(typed.ShapeValidationError) as raised:
            invalid.assert_valid()
        self.assertEqual(raised.exception.report.to_dict(), report.to_dict())


if __name__ == "__main__":
    unittest.main()
