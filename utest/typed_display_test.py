import unittest

from zencad import geom as typed
from zencad.runtime.scene_protocol import decode_brep, decode_json_payload, decode_mesh
from zencad.scene import Scene
from zencad.showapi import disp, display, highlight, hl, managed_scene, show


class TypedManagedDisplayTest(unittest.TestCase):
    def test_managed_scene_retains_typed_sources_until_snapshot(self):
        context = typed.Context.deferred(cache=False)
        shape = context.call(typed.box, 2)
        mesh = shape.to_mesh()
        point = context.call(typed.point3, 1, 2, 3)

        with managed_scene(17):
            shape_ref = display(shape)
            mesh_ref = disp(mesh, display_mode="shaded")
            point_ref = display(point)
            self.assertIs(highlight(shape), shape)
            self.assertIs(hl(point), point)
            snapshot = show()

        self.assertEqual(snapshot.generation, 17)
        self.assertEqual(
            tuple(record.kind for record in snapshot.objects),
            ("brep", "mesh", "point", "brep", "point"),
        )
        self.assertFalse(decode_brep(snapshot.objects[0].payload).IsNull())
        self.assertEqual(decode_mesh(snapshot.objects[1].payload).triangles, list(mesh.triangles))
        self.assertEqual(decode_json_payload(snapshot.objects[2].payload), [1.0, 2.0, 3.0])
        self.assertEqual(mesh_ref._object().display_mode, "shaded")
        self.assertEqual(shape_ref.object_id, "object-000000")
        self.assertEqual(point_ref.object_id, "object-000002")

    def test_direct_scene_materializes_typed_handles_at_interactive_boundary(self):
        context = typed.Context.deferred(cache=False)
        scene = Scene()

        shape_object = scene.add(context.call(typed.box, 1))
        mesh_object = scene.add(context.call(typed.box, 1).to_mesh(), display_mode="wireframe")
        point_object = scene.add(context.call(typed.point3, 1, 2, 3))

        self.assertEqual(type(shape_object).__name__, "ShapeInteractiveObject")
        self.assertEqual(type(mesh_object).__name__, "MeshInteractiveObject")
        self.assertEqual(type(point_object).__name__, "PointInteractiveObject")
        self.assertEqual(mesh_object.mesh_display_mode, "wireframe")


if __name__ == "__main__":
    unittest.main()
