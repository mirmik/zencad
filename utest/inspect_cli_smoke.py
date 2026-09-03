#!/usr/bin/env python3
"""Exercise the headless inspect CLI through an installed ZenCad wheel."""

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def run(root, *arguments, expected=0):
    result = subprocess.run(
        [sys.executable, "-m", "zencad", "inspect", *map(str, arguments)],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
        cwd=root,
        env=os.environ.copy(),
    )
    assert result.returncode == expected, (
        result.returncode,
        result.stdout,
        result.stderr,
    )
    return result


def main():
    assert not any(name.startswith("PyQt5") for name in sys.modules)
    from zencad import inspect_script

    assert not any(name.startswith("PyQt5") for name in sys.modules)
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        model = root / "model.py"
        model.write_text(
            """
import sys
assert not any(name.startswith("PyQt5") for name in sys.modules)
from zencad import box, display, show
print("model stdout")
print("model stderr", file=sys.stderr)
display(box(2, 3, 4).right(5))
show()
""",
            encoding="utf-8",
        )

        first = run(root, model, "--json")
        payload = json.loads(first.stdout)
        assert payload["status"] == "ok"
        assert payload["scene"]["object_count"] == 1
        assert payload["objects"][0]["geometry"]["topology"]["faces"] == 6
        assert "model stdout" in first.stderr
        assert "model stderr" in first.stderr

        second = run(root, model, "--json")
        assert second.stdout == first.stdout

        destination = root / "reports" / "model.json"
        written = run(root, model, "--output", destination)
        assert written.stdout == ""
        assert json.loads(destination.read_text(encoding="utf-8")) == payload

        api_report = inspect_script(model)
        assert api_report.to_dict() == payload
        assert not any(name.startswith("PyQt5") for name in sys.modules)

        graph_path = root / "reports" / "graph.json"
        tree = run(
            root,
            model,
            "--tree",
            "--graph-json",
            graph_path,
            "--no-cache",
        )
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        assert graph["schema"] == "zencad.computation_graph"
        assert graph["status"] == "success"
        assert graph["roots"][0]["id"] == "object-000000"
        assert "zencad.typed.shape.transform" in tree.stdout
        assert "0x" not in tree.stdout

        from zencad import inspect_computation_graph

        api_graph = inspect_computation_graph(model, cache_enabled=False)
        assert api_graph.to_dict()["schema_version"] == 1
        assert len(api_graph.nodes) == 2

        policy_model = root / "policy.py"
        policy_model.write_text(
            """
import sys
from zencad import box, display, show
shape = box(2)
assert shape.context.mode.value == sys.argv[1]
if len(sys.argv) > 2:
    assert shape.context.cache_enabled is (sys.argv[2] == "cache")
display(shape)
show()
""",
            encoding="utf-8",
        )
        deferred_result = run(root, policy_model, "--json", "--", "deferred")
        assert json.loads(deferred_result.stdout)["status"] == "ok"
        eager_result = run(
            root,
            policy_model,
            "--json",
            "--eager",
            "--no-cache",
            "--",
            "immediate",
            "no-cache",
        )
        assert json.loads(eager_result.stdout)["status"] == "ok"
        api_eager = inspect_script(
            policy_model,
            evaluation_mode="immediate",
            cache_enabled=False,
            arguments=("immediate", "no-cache"),
        )
        assert api_eager.to_dict() == json.loads(eager_result.stdout)

        runtime_error = root / "runtime_error.py"
        runtime_error.write_text(
            "raise RuntimeError('inspection broke')\n", encoding="utf-8"
        )
        failed = run(root, runtime_error, "--json", expected=3)
        failure = json.loads(failed.stdout)
        assert failure["status"] == "error"
        assert failure["error"]["code"] == "script_error"
        assert failure["error"]["exception_type"] == "RuntimeError"
        assert "inspection broke" in failure["error"]["message"]

        graph_failure_model = root / "graph_failure.py"
        graph_failure_model.write_text(
            """
from zencad import box, display, show
display(box("bad", 2, 3).right(4))
show()
""",
            encoding="utf-8",
        )
        graph_failure = run(
            root,
            graph_failure_model,
            "--tree",
            "--failed-path",
            "--no-cache",
            expected=3,
        )
        assert "zencad.typed.box [error" in graph_failure.stdout
        assert "zencad.typed.shape.transform [error" in graph_failure.stdout

        syntax_error = root / "syntax_error.py"
        syntax_error.write_text("if True print('broken')\n", encoding="utf-8")
        syntax_failure = run(root, syntax_error, "--json", expected=3)
        assert json.loads(syntax_failure.stdout)["error"]["code"] == "script_error"

        missing_scene = root / "missing_scene.py"
        missing_scene.write_text("value = 42\n", encoding="utf-8")
        missing = run(root, missing_scene, "--json", expected=4)
        assert json.loads(missing.stdout)["error"]["code"] == "missing_scene"

        invalid_geometry = root / "invalid_geometry.py"
        invalid_geometry.write_text(
            """
from OCP.BRep import BRep_Builder
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS_Shell, TopoDS_Solid
from zencad import display, show
from zencad._native.shape import Shape
from zencad.occ_compat import as_face
builder = BRep_Builder()
shell = TopoDS_Shell()
builder.MakeShell(shell)
source = BRepPrimAPI_MakeBox(2, 2, 2).Solid()
builder.Add(shell, as_face(TopExp_Explorer(source, TopAbs_FACE).Current()))
solid = TopoDS_Solid()
builder.MakeSolid(solid)
builder.Add(solid, shell)
display(Shape(solid))
show()
""",
            encoding="utf-8",
        )
        invalid = run(root, invalid_geometry, "--json")
        invalid_payload = json.loads(invalid.stdout)
        assert invalid_payload["objects"][0]["geometry"]["valid"] is False
        assert invalid_payload["objects"][0]["geometry"]["validation"]["issues"]

        timeout = root / "timeout.py"
        timeout.write_text("while True:\n    pass\n", encoding="utf-8")
        timed_out = run(root, timeout, "--json", "--timeout", "0.2", expected=5)
        assert json.loads(timed_out.stdout)["error"]["code"] == "timeout"

    print("ZenCad headless inspect CLI smoke: OK")


if __name__ == "__main__":
    main()
