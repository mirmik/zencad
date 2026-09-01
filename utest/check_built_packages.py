"""Reject bytecode and missing example assets in built distributions."""

import argparse
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

REQUIRED_PACKAGE_PATHS = (
    "zencad/examples/0.Base/helloworld.py",
    "zencad/examples/fonts/testfont.ttf",
    "zencad/zencad_logo.png",
)


def artifact_members(artifact):
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            return archive.namelist()
    if artifact.name.endswith(".tar.gz"):
        with tarfile.open(artifact, "r:gz") as archive:
            return archive.getnames()
    raise ValueError(f"Unsupported distribution artifact: {artifact}")


def normalized_package_paths(members):
    paths = set()
    for member in members:
        path = PurePosixPath(member)
        if path.parts and path.parts[0].startswith("zencad-"):
            path = PurePosixPath(*path.parts[1:])
        paths.add(path.as_posix())
    return paths


def check_artifact(artifact):
    members = artifact_members(artifact)
    forbidden = sorted(
        member
        for member in members
        if "__pycache__" in PurePosixPath(member).parts
        or PurePosixPath(member).suffix in {".pyc", ".pyo"}
    )
    if forbidden:
        raise AssertionError(
            f"{artifact} contains generated Python bytecode: {forbidden}"
        )

    package_paths = normalized_package_paths(members)
    missing = sorted(set(REQUIRED_PACKAGE_PATHS) - package_paths)
    if missing:
        raise AssertionError(
            f"{artifact} is missing required examples/assets: {missing}"
        )

    print(f"Package content smoke: {artifact.name}: OK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", nargs="?", default="dist")
    arguments = parser.parse_args()

    target = Path(arguments.dist)
    artifacts = [target] if target.is_file() else sorted(
        list(target.glob("zencad-*.whl"))
        + list(target.glob("zencad-*.tar.gz"))
    )
    if not artifacts:
        raise SystemExit(f"No ZenCad distribution artifacts found in {target}")

    for artifact in artifacts:
        check_artifact(artifact)


if __name__ == "__main__":
    main()
