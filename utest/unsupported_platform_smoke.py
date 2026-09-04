"""Require pip to explain why an unsupported platform cannot install ZenCad."""

from email.parser import Parser
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile


def wheel_version(wheel):
    with ZipFile(wheel) as archive:
        metadata_files = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_files) != 1:
            raise AssertionError(metadata_files)
        metadata = Parser().parsestr(
            archive.read(metadata_files[0]).decode("utf-8")
        )
    return metadata["Version"]


def main():
    dist_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "dist").resolve()
    wheels = sorted(dist_dir.glob("zencad-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"Expected one ZenCad wheel, found {wheels}")

    with TemporaryDirectory() as download_dir:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--dest",
                download_dir,
                "--only-binary=:all:",
                "--find-links",
                str(dist_dir),
                "--platform",
                "win32",
                "--python-version",
                "3.12",
                "--implementation",
                "cp",
                "--abi",
                "cp312",
                f"zencad=={wheel_version(wheels[0])}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    print(result.stdout)
    assert result.returncode != 0, "Unsupported win32 install unexpectedly succeeded"
    assert "No matching distribution found for cadquery-ocp-novtk" in result.stdout
    print("Unsupported-platform dependency error is actionable: OK")


if __name__ == "__main__":
    main()
