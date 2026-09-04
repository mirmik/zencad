"""Topology selection must not depend on compound child insertion order."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Compound

import zencad as z


def compound(parts, context):
    builder = BRep_Builder()
    native = TopoDS_Compound()
    builder.MakeCompound(native)
    for part in parts:
        builder.Add(native, part.native())
    return z.Compound.from_ocp(native, context=context)


def signature(shape):
    return sorted(tuple(round(c, 7) for c in v.point().value()) for v in shape.vertices())


class TopologyOrderTest(unittest.TestCase):
    def test_child_permutation_preserves_all_query_results_and_selected_geometry(self):
        for mode in ("immediate", "deferred"):
            with self.subTest(mode=mode):
                context = z.Context(mode=mode, cache=False)
                left = context.call(z.box, 2).translate(-5, 0, 0)
                right = context.call(z.box, 2).translate(5, 0, 0)
                forward = compound((left, right), context)
                backward = compound((right, left), context)
                for query in ("vertices", "edges", "wires", "faces", "shells", "solids", "compounds"):
                    with self.subTest(query=query):
                        self.assertEqual(
                            [signature(item) for item in getattr(forward, query)()],
                            [signature(item) for item in getattr(backward, query)()],
                        )
                for body in (forward, backward):
                    # Reversing an already ordered sequence must not change tie resolution.
                    solids = body.solids()[::-1]
                    self.assertAlmostEqual(solids.sort_by(z.Axis.Z)[0].center().x.value(), -4)
                    self.assertAlmostEqual(solids.sort_by_distance((1, 1, 1))[0].center().x.value(), -4)
                    self.assertAlmostEqual(solids.largest().center().x.value(), -4)
                    self.assertEqual(len(body.edges()), 48)
                    self.assertEqual(len(body.vertices()), 16)

    def test_face_only_compounds_have_geometric_centers(self):
        context = z.Context.deferred(cache=False)
        left = compound((context.call(z.rectangle, 2, 2).left(5),), context)
        right = compound((context.call(z.rectangle, 2, 2).right(5),), context)
        forward = compound((left, right), context)
        backward = compound((right, left), context)
        self.assertEqual(
            [signature(item) for item in forward.compounds()],
            [signature(item) for item in backward.compounds()],
        )

    def test_fresh_process_and_disk_cache_preserve_index_selection(self):
        source = '''
import json, sys
import zencad as z
z.configure(cache_dir=sys.argv[1], cache_enabled=sys.argv[2] == "on")
body = z.box(2, 4, 6)
print(json.dumps([v.point().value() for v in body.vertices()]))
'''
        with tempfile.TemporaryDirectory() as directory:
            results = []
            for policy in ("on", "on", "off"):
                result = subprocess.run(
                    [sys.executable, "-c", source, directory, policy],
                    cwd=Path(__file__).parents[1], text=True, capture_output=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                results.append(json.loads(result.stdout))
        expected = [[x, y, zz] for x in (0, 2) for y in (0, 4) for zz in (0, 6)]
        self.assertEqual(results, [expected] * 3)


if __name__ == "__main__":
    unittest.main()
