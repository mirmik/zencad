import json
import unittest

from OCP.BRep import BRep_Builder
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Shell, TopoDS_Solid

import zencad
from zencad._native.shape import Shape
from zencad.check import (
    CheckExpectations,
    NumericRange,
    check_inspection,
)
from zencad.inspect import inspect_snapshot
from zencad.occ_compat import as_face
from zencad.scene_draft import SceneDraft


def _range(value, tolerance=1e-6):
    return NumericRange.exact(value, tolerance=tolerance)


def _open_solid():
    builder = BRep_Builder()
    shell = TopoDS_Shell()
    builder.MakeShell(shell)
    source = BRepPrimAPI_MakeBox(2, 2, 2).Solid()
    explorer = TopExp_Explorer(source, TopAbs_FACE)
    builder.Add(shell, as_face(explorer.Current()))
    solid = TopoDS_Solid()
    builder.MakeSolid(solid)
    builder.Add(solid, shell)
    return solid


class CheckTest(unittest.TestCase):
    def test_single_object_passes_all_basic_expectations(self):
        draft = SceneDraft(generation=1)
        draft.add(zencad.box(2, 3, 4))
        inspection = inspect_snapshot(draft.snapshot(), script_path="model.py")

        report = check_inspection(
            inspection,
            CheckExpectations(
                valid=True,
                kind="brep",
                solid=True,
                volume=_range(24),
                surface_area=_range(52),
                bbox_size=(_range(2), _range(3), _range(4)),
            ),
        )
        payload = report.to_dict()

        self.assertTrue(report.passed)
        self.assertEqual(payload["schema"], "zencad.check")
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(
            payload["summary"], {"check_count": 7, "passed": 7, "failed": 0}
        )
        self.assertEqual(payload["subject"]["kind"], "brep")
        self.assertEqual(payload["subject"]["shape_type"], "solid")
        self.assertEqual(
            [check["name"] for check in payload["checks"]],
            [
                "non_empty",
                "valid",
                "kind",
                "solid",
                "volume",
                "surface_area",
                "bbox_size",
            ],
        )
        self.assertEqual(json.loads(report.to_json()), payload)
        self.assertEqual(report.to_json(), report.to_json())

    def test_multiple_visible_objects_are_aggregated(self):
        draft = SceneDraft(generation=2)
        draft.add(zencad.box(1))
        second = draft.add(zencad.box(2))
        second.right(3)

        report = check_inspection(
            inspect_snapshot(draft.snapshot()),
            CheckExpectations(
                valid=True,
                kind="brep",
                solid=True,
                volume=_range(9),
                surface_area=_range(30),
                bbox_size=(_range(5), _range(2), _range(2)),
            ),
        )

        self.assertTrue(report.passed)
        self.assertEqual(report.subject.object_count, 2)
        self.assertAlmostEqual(report.subject.volume, 9)
        self.assertAlmostEqual(report.subject.surface_area, 30)
        for actual, expected in zip(report.subject.bbox_size, (5, 2, 2)):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_multiple_failures_keep_expected_actual_and_tolerance(self):
        draft = SceneDraft(generation=3)
        draft.add(zencad.point3(1, 2, 3))

        report = check_inspection(
            inspect_snapshot(draft.snapshot()),
            CheckExpectations(
                kind="brep",
                solid=True,
                volume=NumericRange(10, 20, tolerance=0.5),
                surface_area=NumericRange(10, 20, tolerance=0.5),
                bbox_size=(_range(1), _range(1), _range(1)),
            ),
        )
        payload = report.to_dict()
        checks = {check["name"]: check for check in payload["checks"]}

        self.assertFalse(report.passed)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["summary"]["failed"], 5)
        self.assertEqual(checks["kind"]["expected"], "brep")
        self.assertEqual(checks["kind"]["actual"], "point")
        self.assertEqual(
            checks["volume"]["expected"], {"minimum": 10.0, "maximum": 20.0}
        )
        self.assertIsNone(checks["volume"]["actual"])
        self.assertEqual(checks["volume"]["tolerance"], 0.5)
        self.assertEqual(checks["bbox_size"]["actual"], [0.0, 0.0, 0.0])

    def test_valid_failure_embeds_versioned_validation_report(self):
        draft = SceneDraft(generation=4)
        draft.add(Shape(_open_solid()))

        report = check_inspection(
            inspect_snapshot(draft.snapshot()),
            CheckExpectations(valid=True),
        )
        validity = report.to_dict()["checks"][1]
        validation = validity["details"]["objects"][0]["validation"]

        self.assertFalse(validity["passed"])
        self.assertEqual(validation["schema_version"], 1)
        self.assertFalse(validation["valid"])
        self.assertTrue(validation["issues"])

    def test_hidden_only_scene_is_empty_but_remains_counted(self):
        draft = SceneDraft(generation=5)
        draft.add(zencad.box(1)).hide()

        report = check_inspection(inspect_snapshot(draft.snapshot()))

        self.assertFalse(report.passed)
        self.assertEqual(report.subject.object_count, 0)
        self.assertEqual(report.subject.total_object_count, 1)
        self.assertEqual(report.checks[0].name, "non_empty")
        self.assertFalse(report.checks[0].passed)

    def test_range_and_expectation_validation(self):
        self.assertTrue(NumericRange(None, 10, tolerance=0.1).contains(10.1))
        self.assertTrue(NumericRange(10, None).contains(10))
        self.assertFalse(NumericRange(10, 20).contains(None))
        with self.assertRaises(ValueError):
            NumericRange()
        with self.assertRaises(ValueError):
            NumericRange(2, 1)
        with self.assertRaises(ValueError):
            NumericRange(1, 2, tolerance=-1)
        with self.assertRaises(TypeError):
            CheckExpectations(volume=(1, 2))
        with self.assertRaises(TypeError):
            CheckExpectations(bbox_size=(_range(1), _range(2)))
        with self.assertRaises(TypeError):
            CheckExpectations(non_empty=None)


if __name__ == "__main__":
    unittest.main()
