from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from evalcache.dircache_v2 import DirCache_v2
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
import zencad
from zencad.occ_compat import add_to_bounds, volume_properties
from zencad.runtime.scene_protocol import (
    decode_brep,
    decode_snapshot_frame,
    encode_snapshot_frame,
)
from zencad.scene_draft import SceneDraft


ROOT = Path(__file__).parents[1]


def shape_signature(shape):
    properties = GProp_GProps()
    volume_properties(shape, properties)
    bounds = Bnd_Box()
    add_to_bounds(shape, bounds)
    return properties.Mass(), bounds.Get()


class SceneDraftTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache_directory = TemporaryDirectory()
        zencad.lazy.cache = DirCache_v2(cls.cache_directory.name)
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    @classmethod
    def tearDownClass(cls):
        cls.cache_directory.cleanup()

    def test_mutations_are_frozen_into_snapshot_properties(self):
        draft = SceneDraft(generation=4)
        reference = draft.add(zencad.box(2).unlazy(), color=(0.1, 0.2, 0.3, 0.4))
        reference.relocate(zencad.translate(5, 6, 7))
        reference.set_color(
            0.7,
            0.6,
            0.5,
            0.4,
            border_color=(0.3, 0.2, 0.1, 0),
            wire_color=(0.9, 0.8, 0.7, 0),
        )
        reference.hide(True)

        snapshot = draft.snapshot()
        record = snapshot.objects[0]
        properties = record.properties
        self.assertEqual(reference.object_id, "object-000000")
        self.assertEqual(record.kind, "brep")
        self.assertEqual(properties["color"], (0.7, 0.6, 0.5, 0.4))
        self.assertEqual(properties["border_color"], (0.3, 0.2, 0.1, 0))
        self.assertEqual(properties["wire_color"], (0.9, 0.8, 0.7, 0))
        self.assertFalse(properties["visible"])
        self.assertEqual(properties["transform"]["translation"], (5, 6, 7))
        self.assertFalse(decode_brep(record.payload).IsNull())

        reference.hide(False).set_color(1, 1, 1)
        self.assertFalse(properties["visible"])
        self.assertEqual(properties["color"], (0.7, 0.6, 0.5, 0.4))

    def test_managed_public_api_publishes_without_legacy_viewer(self):
        published = []
        with mock.patch("zencad.settings.Settings.restore") as restore:
            with zencad.managed_scene(11, published.append) as draft:
                reference = zencad.display(zencad.box(3), color=zencad.color.red)
                reference.right(2)
                snapshot = zencad.show()

        restore.assert_not_called()
        self.assertIs(snapshot, published[0])
        self.assertEqual(snapshot.generation, 11)
        self.assertEqual(len(draft), 1)
        self.assertEqual(
            decode_snapshot_frame(encode_snapshot_frame(snapshot)),
            snapshot,
        )

    def test_generations_are_isolated(self):
        published = []
        with zencad.managed_scene(20, published.append):
            first = zencad.display(zencad.box(1))
            first.set_color(1, 0, 0)
            zencad.show()
        with zencad.managed_scene(21, published.append):
            second = zencad.display(zencad.sphere(2))
            second.set_color(0, 1, 0)
            zencad.show()

        self.assertEqual([item.generation for item in published], [20, 21])
        self.assertEqual(
            published[0].objects[0].properties["color"],
            (1, 0, 0, 0),
        )
        self.assertEqual(
            published[1].objects[0].properties["color"],
            (0, 1, 0, 0),
        )
        self.assertNotEqual(
            published[0].objects[0].payload,
            published[1].objects[0].payload,
        )

    def test_static_example_produces_complete_snapshot(self):
        published = []
        example = ROOT / "zencad" / "examples" / "0.Base" / "helloworld.py"
        with zencad.managed_scene(30, published.append):
            with redirect_stdout(io.StringIO()):
                namespace = runpy.run_path(str(example), run_name="__main__")

        self.assertEqual(len(published), 1)
        self.assertEqual(len(published[0].objects), 1)
        restored = decode_brep(published[0].objects[0].payload)
        expected = namespace["model"].unlazy().Shape()
        restored_mass, restored_bounds = shape_signature(restored)
        expected_mass, expected_bounds = shape_signature(expected)
        self.assertAlmostEqual(
            restored_mass,
            expected_mass,
            delta=max(1e-8, abs(expected_mass) * 1e-12),
        )
        for actual, wanted in zip(restored_bounds, expected_bounds):
            self.assertAlmostEqual(actual, wanted, places=8)

    def test_managed_path_does_not_import_qt_or_create_ais_shape(self):
        code = r'''
import builtins
real_import = builtins.__import__
def guarded_import(name, *args, **kwargs):
    if name == "PyQt5" or name.startswith("PyQt5."):
        raise AssertionError("managed runner imported PyQt5")
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded_import

import zencad
import zencad.interactive.shape
zencad.lazy.encache = False
zencad.lazy.decache = False
zencad.lazy.fastdo = True
def forbidden_ais_shape(*args, **kwargs):
    raise AssertionError("managed runner created AIS_Shape")
zencad.interactive.shape.AIS_Shape = forbidden_ais_shape

published = []
with zencad.managed_scene(1, published.append):
    ref = zencad.display(zencad.box(1))
    ref.relocate(zencad.translate(1, 2, 3))
    zencad.show()
assert len(published) == 1
'''
        subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
