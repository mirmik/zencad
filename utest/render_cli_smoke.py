#!/usr/bin/env python3
"""Exercise deterministic CLI previews through an installed ZenCad wheel."""

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def run(*arguments, expected=0):
    result = subprocess.run(
        [sys.executable, "-m", "zencad", "render", *map(str, arguments)],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env=os.environ.copy(),
    )
    assert result.returncode == expected, (
        result.returncode,
        result.stdout,
        result.stderr,
    )
    return result


def main():
    from PyQt5.QtGui import QImage
    from zencad import render_script

    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        model = root / "model.py"
        model.write_text(
            """
from zencad import box, cylinder, display, show
display(box(20, 12, 8) - cylinder(3, 8).up(2), color=(0.2, 0.5, 0.8, 0))
show()
""",
            encoding="utf-8",
        )
        first = root / "preview-one.png"
        second = root / "preview-two.png"
        common = (
            model,
            "--views", "iso,front,top,right",
            "--size", "160x120",
            "--background", "#123456",
        )
        run(*common, "--output", first)
        api_result = render_script(
            model,
            second,
            views=("iso", "front", "top", "right"),
            size=(160, 120),
            background="#123456",
        )
        assert api_result.path == second.resolve()
        assert api_result.image_size == (320, 240)

        image = QImage(str(first))
        assert not image.isNull()
        assert (image.width(), image.height()) == (320, 240)
        assert first.read_bytes() == second.read_bytes()

        background = (0x12, 0x34, 0x56)
        background_samples = 0
        geometry_samples = 0
        for x in range(0, image.width(), 4):
            for y in range(0, image.height(), 4):
                color = image.pixelColor(x, y)
                rgb = (color.red(), color.green(), color.blue())
                if all(
                    abs(actual - expected) <= 1
                    for actual, expected in zip(rgb, background)
                ):
                    background_samples += 1
                elif max(rgb) - min(rgb) > 12:
                    geometry_samples += 1
        assert background_samples > 400, background_samples
        assert geometry_samples > 150, geometry_samples

        for mode in ("shaded", "wireframe"):
            mode_path = root / f"{mode}.png"
            run(
                model,
                "-o", mode_path,
                "--size", "96x64",
                "--mode", mode,
                "--axes",
            )
            mode_image = QImage(str(mode_path))
            assert not mode_image.isNull()
            assert (mode_image.width(), mode_image.height()) == (96, 64)

        empty = root / "empty.py"
        empty.write_text("from zencad import show\nshow()\n", encoding="utf-8")
        empty_result = run(empty, "-o", root / "empty.png", expected=4)
        assert "no visible scene objects" in empty_result.stderr.lower()

        failing = root / "failing.py"
        failing.write_text("raise RuntimeError('preview broke')\n", encoding="utf-8")
        failure = run(failing, "-o", root / "failed.png", expected=3)
        assert "preview broke" in failure.stderr
        assert not (root / "failed.png").exists()

        animated = root / "animated.py"
        animated.write_text(
            """
from zencad import box, display, show
display(box(1))
def animate(state):
    pass
show(animate=animate, animate_step=0.01)
""",
            encoding="utf-8",
        )
        animation = run(
            animated,
            "-o",
            root / "animated.png",
            expected=3,
        )
        assert "cannot be rendered as a static preview" in animation.stderr

    print("ZenCad deterministic render CLI smoke: OK")


if __name__ == "__main__":
    main()
