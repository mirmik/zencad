from pathlib import Path
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).parents[1]


class EvaluationPolicyTest(unittest.TestCase):
    def run_script(self, source):
        process = subprocess.run(
            [sys.executable, "-c", textwrap.dedent(source)],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_global_mode_preserves_handle_ownership_and_types(self):
        self.run_script('''
            import zencad as z
            z.configure(cache_enabled=False)
            body = z.box(10)
            assert z.evaluation_mode().value == "deferred"
            assert z.set_evaluation_mode("immediate") is None
            hole = z.box(2)
            assert body.context is hole.context
            assert type(body) is type(hole) is z.Solid
            assert abs((body - hole).mass().value() - 992) < 1e-6
            z.set_evaluation_mode(z.EvaluationMode.DEFERRED)
            assert z.box(3).context is body.context
        ''')

    def test_immediate_reports_errors_at_construction(self):
        self.run_script('''
            import zencad as z
            from OCP.Standard import Standard_ConstructionError
            z.configure(cache_enabled=False)
            bad = z.sphere(-1)
            try:
                bad.native()
            except Standard_ConstructionError:
                pass
            else:
                raise AssertionError("deferred geometry must fail at materialization")
            z.set_evaluation_mode("immediate")
            try:
                z.sphere(-1)
            except Standard_ConstructionError:
                pass
            else:
                raise AssertionError("immediate geometry must fail at construction")
        ''')

    def test_cache_configuration_preserves_selected_mode_and_is_qt_free(self):
        self.run_script('''
            import sys, zencad as z
            z.set_evaluation_mode("immediate")
            z.configure(cache_enabled=False)
            assert z.evaluation_mode().value == "immediate"
            assert not z.box(2).context.cache_enabled
            assert not any(n.startswith("PyQt5") for n in sys.modules)
            for name in ("eager", "immediate", "deferred", "evaluation"):
                assert not hasattr(z, name), name
            try:
                z.set_evaluation_mode("eventually")
            except ValueError:
                pass
            else:
                raise AssertionError("invalid mode accepted")
            assert z.evaluation_mode().value == "immediate"
        ''')

    def test_script_header_overrides_runner_mode_and_preserves_graph_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "model.py"
            graph_path = Path(directory) / "graph.json"
            script.write_text('''import zencad as z
assert z.evaluation_mode().value == "deferred"
z.set_evaluation_mode("immediate")
assert z.evaluation_mode().value == "immediate"
z.display(z.box(2), name="part")
z.show()
''')
            result = subprocess.run(
                [sys.executable, "-m", "zencad", "inspect", str(script),
                 "--no-cache", "--json", "--graph-json", str(graph_path)],
                cwd=ROOT, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertAlmostEqual(
                json.loads(result.stdout)["objects"][0]["geometry"]["volume"], 8
            )
            graph = json.loads(graph_path.read_text())
            self.assertTrue(graph["nodes"])
            self.assertTrue(any(node["operation"] == "zencad.typed.box" for node in graph["nodes"]))


if __name__ == "__main__":
    unittest.main()
