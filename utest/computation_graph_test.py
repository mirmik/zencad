from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import zencad
from zencad.cache_config import current_cache_configuration
from zencad.computation_graph import ComputationGraph


class ComputationGraphTest(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.previous_cache = current_cache_configuration()
        zencad.configure(
            cache_dir=self.root / "cache",
            cache_enabled=True,
        )

    def tearDown(self):
        zencad.configure(
            cache_dir=self.previous_cache.directory,
            cache_enabled=self.previous_cache.enabled,
        )
        self.directory.cleanup()

    def script(self, name, source):
        path = self.root / name
        path.write_text(source, encoding="utf-8")
        return path

    def test_branching_shared_graph_has_stable_ids_and_cache_state(self):
        model = self.script(
            "shared.py",
            """
from zencad import box, display, show
base = box(2, 3, 4)
left = base.left(5)
right = base.right(5)
display(left + right)
show()
""",
        )

        first = zencad.inspect_computation_graph(model)
        second = zencad.inspect_computation_graph(model)

        self.assertEqual(first.execution_status, "success")
        self.assertEqual(len(first.roots), 1)
        self.assertEqual(len(first.nodes), 4)
        self.assertEqual(
            [(node.node_id, node.dependencies) for node in first.nodes],
            [(node.node_id, node.dependencies) for node in second.nodes],
        )
        box_node = next(
            node for node in first.nodes if node.operation == "zencad.typed.box"
        )
        transforms = [
            node
            for node in first.nodes
            if node.operation == "zencad.typed.shape.transform"
        ]
        self.assertEqual(len(transforms), 2)
        self.assertTrue(
            all(box_node.node_id in node.dependencies for node in transforms)
        )
        self.assertTrue(any(node.cache == "hit" for node in second.nodes))
        self.assertEqual(first.to_json(), first.to_json())
        self.assertNotIn("0x", first.to_tree())
        self.assertTrue(all(node.source_file == str(model) for node in first.nodes))

        hidden = first.filtered(hide_literals=True)
        hidden_box = next(
            node for node in hidden.nodes if node.operation == "zencad.typed.box"
        )
        self.assertEqual(hidden_box.arguments, ())

        root_only = hidden.filtered(max_depth=0)
        self.assertEqual(len(root_only.nodes), 1)
        self.assertTrue(
            all(not argument.literal for argument in root_only.nodes[0].arguments)
        )

        payload = first.to_dict()
        self.assertEqual(ComputationGraph.from_dict(payload).to_dict(), payload)

    def test_failed_path_is_returned_for_evaluation_exception(self):
        model = self.script(
            "failed.py",
            """
from zencad import box, display, show
display(box("bad", 2, 3).right(4))
show()
""",
        )

        graph = zencad.inspect_computation_graph(model, cache_enabled=False)
        failed = graph.filtered(failed_path=True)

        self.assertEqual(graph.execution_status, "error")
        self.assertEqual(len(failed.nodes), 2)
        self.assertTrue(all(node.evaluation == "error" for node in failed.nodes))
        self.assertIn("could not convert string", graph.to_json())

    def test_capture_limit_is_reported_without_changing_evaluation(self):
        model = self.script(
            "limited.py",
            """
from zencad import box, display, show
shape = box(1)
for index in range(12):
    shape = shape.right(index + 1)
display(shape)
show()
""",
        )

        graph = zencad.inspect_computation_graph(
            model,
            cache_enabled=False,
            max_nodes=3,
        )

        self.assertEqual(graph.execution_status, "success")
        self.assertTrue(graph.truncated)
        self.assertLessEqual(len(graph.nodes), 3)
        self.assertEqual(graph.node_limit, 3)


if __name__ == "__main__":
    unittest.main()
