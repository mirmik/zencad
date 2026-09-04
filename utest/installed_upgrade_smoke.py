"""Smoke an upgrade from the last published ZenCad to the release candidate."""

import importlib.metadata
import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import zencad


def main():
    assert zencad.__version__ == "2.0.0"
    assert zencad.__version__ == importlib.metadata.version("zencad")

    checkout = os.environ.get("GITHUB_WORKSPACE")
    if checkout:
        package_path = Path(zencad.__file__).resolve()
        assert not package_path.is_relative_to(Path(checkout).resolve())

    # The pip-only release must not acquire the former pythonocc namespace.
    assert importlib.util.find_spec("OCC") is None

    with TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        zencad.configure(cache_dir=temporary_path / "cache")

        shape = zencad.box(4, 5, 6) - zencad.sphere(1)
        brep_path = temporary_path / "upgrade-smoke.brep"
        zencad.to_brep(shape, brep_path)
        restored = zencad.from_brep(brep_path)
        assert abs(restored.mass().value() - shape.mass().value()) < 1e-8

        font_path = (
            Path(zencad.__file__).resolve().parent
            / "examples"
            / "fonts"
            / "mandarinc.ttf"
        )
        zencad.register_font(font_path)
        text = zencad.textshape("Upgrade", "MandarinC", 10)
        assert len(text.edges()) > 0

    print("Upgrade from zencad 1.3.3 to 2.0.0 release candidate: OK")


if __name__ == "__main__":
    main()
