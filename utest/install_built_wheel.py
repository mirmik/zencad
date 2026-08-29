#!/usr/bin/env python3
"""Install the single ZenCad wheel produced by the distribution build."""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--dist-dir", default="dist")
    arguments = parser.parse_args()

    wheels = sorted(Path(arguments.dist_dir).glob("zencad-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(
            f"Expected exactly one ZenCad wheel in {arguments.dist_dir!r}, "
            f"found {len(wheels)}: {wheels}"
        )

    requirement = str(wheels[0].resolve())
    if arguments.gui:
        requirement = f"{requirement}[gui]"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--only-binary=:all:",
            requirement,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
