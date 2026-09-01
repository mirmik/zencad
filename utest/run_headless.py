"""Run the complete headless suite without sharing mutable global cache state."""

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main():
    environment = os.environ.copy()
    python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(ROOT) + (
        os.pathsep + python_path if python_path else ""
    )

    isolated_modules = ("import_test.py", "migration_baseline_test.py")
    for module in isolated_modules:
        subprocess.run(
            [sys.executable, str(ROOT / "utest" / module)],
            cwd=ROOT,
            env=environment,
            check=True,
        )

    import zencad

    with TemporaryDirectory() as cache_directory:
        zencad.configure(cache_dir=cache_directory, cache_enabled=True)
        discovered = unittest.defaultTestLoader.discover(
            str(ROOT / "utest"), pattern="*_test.py"
        )
        suite = unittest.TestSuite(
            test
            for test in flatten(discovered)
            if test.__class__.__module__
            not in {"import_test", "migration_baseline_test"}
        )
        result = unittest.TextTestRunner(verbosity=1).run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
