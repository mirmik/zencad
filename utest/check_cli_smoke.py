#!/usr/bin/env python3
"""Exercise headless inspect/check through an installed ZenCad wheel."""

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def run(root, command, *arguments, expected=0):
    result = subprocess.run(
        [sys.executable, "-m", "zencad", command, *map(str, arguments)],
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
    from zencad import CheckExpectations, NumericRange, check_script

    assert not any(name.startswith("PyQt5") for name in sys.modules)
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        model = root / "model.py"
        model.write_text(
            """
import sys
assert not any(name.startswith("PyQt5") for name in sys.modules)
from zencad import box, display, show
shape = box(2, 3, 4)
assert shape.context.mode.value == sys.argv[1]
assert shape.context.cache_enabled is (sys.argv[2] == "cache")
print("model stdout")
print("model stderr", file=sys.stderr)
display(shape)
show()
""",
            encoding="utf-8",
        )

        inspected = run(root, "inspect", model, "--json", "--", "deferred", "cache")
        assert json.loads(inspected.stdout)["status"] == "ok"

        success = run(
            root,
            "check",
            model,
            "--valid",
            "--kind",
            "brep",
            "--solid",
            "--volume",
            "24",
            "--area",
            "52",
            "--bbox-size",
            "2,3,4",
            "--tolerance",
            "0.000001",
            "--eager",
            "--no-cache",
            "--json",
            "--",
            "immediate",
            "no-cache",
        )
        payload = json.loads(success.stdout)
        assert payload["schema"] == "zencad.check"
        assert payload["schema_version"] == 1
        assert payload["status"] == "passed"
        assert payload["summary"] == {"check_count": 7, "failed": 0, "passed": 7}
        assert "model stdout" in success.stderr
        assert "model stderr" in success.stderr
        assert not any(name.startswith("PyQt5") for name in sys.modules)

        def exact(value):
            return NumericRange.exact(value, tolerance=0.000001)

        api_report = check_script(
            model,
            CheckExpectations(
                valid=True,
                kind="brep",
                solid=True,
                volume=exact(24),
                surface_area=exact(52),
                bbox_size=(exact(2), exact(3), exact(4)),
            ),
            evaluation_mode="immediate",
            cache_enabled=False,
            arguments=("immediate", "no-cache"),
        )
        assert api_report.to_dict() == payload

        destination = root / "reports" / "check.json"
        written = run(
            root,
            "check",
            model,
            "--volume",
            "1:2",
            "--bbox-size",
            "0:1,0:1,0:1",
            "--output",
            destination,
            "--",
            "deferred",
            "cache",
            expected=7,
        )
        assert written.stdout == ""
        failure = json.loads(destination.read_text(encoding="utf-8"))
        assert failure["status"] == "failed"
        assert failure["summary"]["failed"] == 2
        assert {
            check["name"] for check in failure["checks"] if not check["passed"]
        } == {"volume", "bbox_size"}

        runtime_error = root / "runtime_error.py"
        runtime_error.write_text(
            "raise RuntimeError('check broke')\n", encoding="utf-8"
        )
        failed = run(root, "check", runtime_error, "--valid", "--json", expected=3)
        error = json.loads(failed.stdout)
        assert error["status"] == "error"
        assert error["error"]["code"] == "script_error"
        assert error["error"]["exception_type"] == "RuntimeError"

        missing_scene = root / "missing_scene.py"
        missing_scene.write_text("value = 42\n", encoding="utf-8")
        missing = run(root, "check", missing_scene, "--json", expected=4)
        assert json.loads(missing.stdout)["error"]["code"] == "missing_scene"

        timeout = root / "timeout.py"
        timeout.write_text("while True:\n    pass\n", encoding="utf-8")
        timed_out = run(
            root,
            "check",
            timeout,
            "--json",
            "--timeout",
            "0.2",
            expected=5,
        )
        assert json.loads(timed_out.stdout)["error"]["code"] == "timeout"

        invalid_usage = run(
            root,
            "check",
            model,
            "--volume",
            ":",
            expected=2,
        )
        assert invalid_usage.stdout == ""
        assert "expected NUMBER" in invalid_usage.stderr

    print("ZenCad headless check CLI smoke: OK")


if __name__ == "__main__":
    main()
