import json
import unittest

from OCP.BRep import BRep_Builder
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Compound, TopoDS_Shell, TopoDS_Solid

import zencad
from zencad._native.mesh import MeshData
from zencad._native.shape import Shape
from zencad.inspect import GeometryInspectionError, inspect_snapshot
from zencad.interactive.line import line
from zencad.occ_compat import as_face
from zencad.runtime.scene_protocol import SceneObjectRecord, SceneSnapshot
from zencad.scene_draft import SceneDraft


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


class InspectSnapshotTest(unittest.TestCase):
    def test_reports_brep_mesh_point_and_line_geometry(self):
        draft = SceneDraft(generation=7)
        body = draft.add(zencad.box(2, 3, 4))
        body.right(10)
        draft.add(MeshData(
            positions=[(0, 0, 0), (2, 0, 0), (0, 2, 0)],
            normals=[(0, 0, 1)] * 3,
            triangles=[(0, 1, 2)],
            triangle_face_ids=[0],
        ), display_mode="wireframe")
        draft.add(zencad.point3(1, 2, 3))
        draft.add(line((0, 0, 0), (0, 3, 4)))

        report = inspect_snapshot(draft.snapshot({"purpose": "test"}))
        payload = report.to_dict()

        self.assertEqual(payload["schema"], "zencad.inspect")
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["scene"]["object_count"], 4)
        self.assertEqual(payload["scene"]["metadata"], {"purpose": "test"})
        self.assertEqual(
            [item["id"] for item in payload["objects"]],
            [f"object-{index:06d}" for index in range(4)],
        )

        brep = payload["objects"][0]
        self.assertEqual(brep["kind"], "brep")
        self.assertEqual(brep["geometry"]["shape_type"], "solid")
        self.assertAlmostEqual(brep["geometry"]["volume"], 24)
        self.assertAlmostEqual(brep["geometry"]["surface_area"], 52)
        self.assertEqual(
            brep["geometry"]["topology"],
            {
                "vertices": 8,
                "edges": 12,
                "wires": 6,
                "faces": 6,
                "shells": 1,
                "solids": 1,
                "compsolids": 0,
                "compounds": 0,
            },
        )
        self.assertTrue(brep["geometry"]["valid"])
        self.assertEqual(
            brep["presentation"]["transform"]["translation"],
            [10.0, 0.0, 0.0],
        )
        for actual, expected in zip(
            brep["geometry"]["bbox"]["size"], (2, 3, 4)
        ):
            self.assertAlmostEqual(actual, expected, places=5)

        mesh = payload["objects"][1]
        self.assertEqual(mesh["presentation"]["display_mode"], "wireframe")
        self.assertEqual(mesh["geometry"]["vertex_count"], 3)
        self.assertEqual(mesh["geometry"]["triangle_count"], 1)
        self.assertAlmostEqual(mesh["geometry"]["surface_area"], 2)
        self.assertTrue(mesh["geometry"]["valid"])

        self.assertEqual(
            payload["objects"][2]["geometry"]["coordinates"],
            [1.0, 2.0, 3.0],
        )
        self.assertAlmostEqual(payload["objects"][3]["geometry"]["length"], 5)
        self.assertEqual(json.loads(report.to_json()), payload)
        self.assertEqual(report.to_json(), report.to_json())

    def test_invalid_shapes_and_degenerate_meshes_remain_inspectable(self):
        draft = SceneDraft(generation=8)
        draft.add(Shape(_open_solid()))
        draft.add(MeshData(
            positions=[(0, 0, 0), (1, 0, 0), (2, 0, 0)],
            normals=[(0, 0, 1)] * 3,
            triangles=[(0, 1, 2)],
            triangle_face_ids=[0],
        ))

        objects = inspect_snapshot(draft.snapshot()).to_dict()["objects"]

        self.assertFalse(objects[0]["geometry"]["valid"])
        self.assertEqual(
            objects[0]["geometry"]["validation"]["issues"][0]["code"],
            "not_closed",
        )
        self.assertFalse(objects[1]["geometry"]["valid"])
        self.assertEqual(
            objects[1]["geometry"]["degenerate_triangle_count"], 1
        )

    def test_compound_reports_aggregate_topology_and_properties(self):
        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)
        builder.Add(compound, BRepPrimAPI_MakeBox(1, 1, 1).Solid())
        builder.Add(compound, BRepPrimAPI_MakeBox(2, 1, 1).Solid())
        draft = SceneDraft(generation=9)
        draft.add(Shape(compound))

        geometry = inspect_snapshot(draft.snapshot()).objects[0].geometry

        self.assertEqual(geometry["shape_type"], "compound")
        self.assertEqual(geometry["topology"]["compounds"], 1)
        self.assertEqual(geometry["topology"]["solids"], 2)
        self.assertAlmostEqual(geometry["volume"], 3)
        self.assertTrue(geometry["valid"])

    def test_decode_failures_identify_the_scene_object(self):
        snapshot = SceneSnapshot(
            generation=10,
            objects=(SceneObjectRecord("broken-body", "brep", b"bad"),),
        )

        with self.assertRaises(GeometryInspectionError) as raised:
            inspect_snapshot(snapshot)

        self.assertEqual(raised.exception.object_id, "broken-body")
        self.assertIn("broken-body", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
