#!/usr/bin/env python3
"""Install the single ZenCad wheel produced by the distribution build."""

import argparse
from email.parser import Parser
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile


def wheel_version(wheel):
    with ZipFile(wheel) as archive:
        metadata_files = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_files) != 1:
            raise SystemExit(
                f"Expected exactly one METADATA file in {wheel}, "
                f"found {metadata_files}"
            )
        metadata = Parser().parsestr(
            archive.read(metadata_files[0]).decode("utf-8")
        )
    return metadata["Version"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--examples", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--upgrade", action="store_true")
    parser.add_argument("--dist-dir", default="dist")
    arguments = parser.parse_args()

    wheels = sorted(Path(arguments.dist_dir).glob("zencad-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(
            f"Expected exactly one ZenCad wheel in {arguments.dist_dir!r}, "
            f"found {len(wheels)}: {wheels}"
        )

    requirement = "zencad"
    extras = []
    if arguments.gui:
        extras.append("gui")
    if arguments.examples:
        extras.append("examples")
    if arguments.test:
        extras.append("test")
    if extras:
        requirement = f"{requirement}[{','.join(extras)}]"
    requirement = f"{requirement}=={wheel_version(wheels[0])}"

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--only-binary=:all:",
        "--find-links",
        str(wheels[0].parent.resolve()),
    ]
    if arguments.upgrade:
        command.append("--upgrade")
    command.append(requirement)
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
