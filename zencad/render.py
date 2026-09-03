"""Deterministic PNG previews for managed ZenCad scripts."""

from dataclasses import dataclass
import math
import os
from pathlib import Path
import sys
import tempfile
import threading
from typing import Callable, Iterable

from zencad.runtime.script_evaluator import (
    AnimatedScriptError,
    MissingSceneError,
    ScriptExecutionError,
    ScriptTimeoutError,
    evaluate_static_script,
)


VIEW_NAMES = (
    "iso",
    "front",
    "back",
    "left",
    "right",
    "top",
    "bottom",
)
DISPLAY_MODES = ("shaded", "shaded-with-edges", "wireframe")


class RenderError(RuntimeError):
    """Base class for preview failures."""


class RenderScriptError(RenderError):
    """The model script failed or requested an unsupported live session."""


class EmptySceneError(RenderError):
    """The script did not publish any visible scene objects."""


class RenderTimeoutError(RenderError):
    """The model script did not complete in the requested time."""


class RenderEnvironmentError(RenderError):
    """The native preview renderer cannot start in this environment."""


@dataclass(frozen=True)
class RenderResult:
    path: Path
    views: tuple[str, ...]
    tile_size: tuple[int, int]
    image_size: tuple[int, int]


def parse_views(value: str | Iterable[str]) -> tuple[str, ...]:
    """Normalize a comma-separated string or iterable of fixed view names."""
    if isinstance(value, str):
        raw_values = (value,)
    else:
        raw_values = tuple(value)
    views = tuple(
        name.strip().lower()
        for raw in raw_values
        for name in str(raw).split(",")
        if name.strip()
    )
    if not views:
        raise ValueError("At least one view is required")
    unknown = tuple(name for name in views if name not in VIEW_NAMES)
    if unknown:
        raise ValueError(
            "Unknown view {} (choose from {})".format(
                ", ".join(repr(name) for name in unknown),
                ", ".join(VIEW_NAMES),
            )
        )
    if len(set(views)) != len(views):
        raise ValueError("View names must not be repeated")
    return views


def parse_size(value: str | Iterable[int]) -> tuple[int, int]:
    """Normalize per-view pixel dimensions."""
    if isinstance(value, str):
        parts = value.lower().split("x")
        if len(parts) != 2:
            raise ValueError("Size must have the form WIDTHxHEIGHT")
        try:
            width, height = (int(part) for part in parts)
        except ValueError as exception:
            raise ValueError("Size must have the form WIDTHxHEIGHT") from exception
    else:
        try:
            width, height = value
        except (TypeError, ValueError) as exception:
            raise ValueError("Size must contain width and height") from exception
    if (
        isinstance(width, bool)
        or isinstance(height, bool)
        or not isinstance(width, int)
        or not isinstance(height, int)
        or not 32 <= width <= 16384
        or not 32 <= height <= 16384
    ):
        raise ValueError("Width and height must be integers from 32 to 16384")
    return width, height


def parse_background(value) -> tuple[float, float, float]:
    """Normalize ``#RRGGBB`` or three 0..1 components."""
    if isinstance(value, str):
        text = value.strip()
        if len(text) != 7 or not text.startswith("#"):
            raise ValueError("Background must have the form #RRGGBB")
        try:
            channels = tuple(int(text[index:index + 2], 16) for index in (1, 3, 5))
        except ValueError as exception:
            raise ValueError("Background must have the form #RRGGBB") from exception
        return tuple(channel / 255 for channel in channels)
    try:
        channels = tuple(value)
    except TypeError as exception:
        raise ValueError("Background must contain three components") from exception
    if len(channels) != 3 or any(
        isinstance(channel, bool)
        or not isinstance(channel, (int, float))
        or not math.isfinite(channel)
        or not 0 <= channel <= 1
        for channel in channels
    ):
        raise ValueError("Background components must be numbers from 0 to 1")
    return tuple(float(channel) for channel in channels)


def contact_sheet_grid(count: int) -> tuple[int, int]:
    """Return deterministic near-square ``(columns, rows)`` dimensions."""
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ValueError("Contact sheet requires at least one image")
    columns = math.ceil(math.sqrt(count))
    return columns, math.ceil(count / columns)


def _evaluate_script(
    script_path,
    arguments,
    timeout,
    output: Callable[[str, str], None] | None,
):
    try:
        snapshot = evaluate_static_script(
            script_path,
            arguments=arguments,
            timeout=timeout,
            output=output,
        ).snapshot
        if not any(
            record.properties.get("visible", True)
            for record in snapshot.objects
        ):
            raise EmptySceneError("Script produced no visible scene objects")
        return snapshot
    except ScriptTimeoutError as exception:
        raise RenderTimeoutError(str(exception)) from exception
    except MissingSceneError as exception:
        raise EmptySceneError(str(exception)) from exception
    except (AnimatedScriptError, ScriptExecutionError) as exception:
        message = str(exception)
        if isinstance(exception, AnimatedScriptError):
            message = (
                "Animated show() sessions cannot be rendered as a static "
                "preview"
            )
        raise RenderScriptError(message) from exception


def _orientation_values():
    from OCP.V3d import V3d_TypeOfOrientation

    return {
        "iso": V3d_TypeOfOrientation.V3d_TypeOfOrientation_Zup_AxoRight,
        "front": V3d_TypeOfOrientation.V3d_TypeOfOrientation_Zup_Front,
        "back": V3d_TypeOfOrientation.V3d_TypeOfOrientation_Zup_Back,
        "left": V3d_TypeOfOrientation.V3d_TypeOfOrientation_Zup_Left,
        "right": V3d_TypeOfOrientation.V3d_TypeOfOrientation_Zup_Right,
        "top": V3d_TypeOfOrientation.V3d_TypeOfOrientation_Zup_Top,
        "bottom": V3d_TypeOfOrientation.V3d_TypeOfOrientation_Zup_Bottom,
    }


def _apply_display_mode(widget, display_mode):
    from OCP.AIS import AIS_Shaded, AIS_WireFrame
    from zencad.color import Color
    from zencad.interactive.mesh import configure_mesh_presentation

    for item in widget.scene_presenter.objects:
        if item.kind == "brep":
            item.ais_object.Attributes().SetFaceBoundaryDraw(
                display_mode == "shaded-with-edges"
            )
            widget.Context.SetDisplayMode(
                item.ais_object,
                AIS_WireFrame if display_mode == "wireframe" else AIS_Shaded,
                False,
            )
        elif item.kind == "mesh":
            configure_mesh_presentation(
                item.ais_object,
                display_mode,
                Color(item.properties["color"]).to_Quantity_Color(),
                Color(item.properties["border_color"]).to_Quantity_Color(),
            )
            widget.Context.SetDisplayMode(item.ais_object, 0, False)
            widget.Context.Redisplay(item.ais_object, False)
    widget.Context.UpdateCurrentViewer()


def _check_render_environment():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()
    if sys.platform.startswith("linux"):
        if not os.environ.get("DISPLAY"):
            raise RenderEnvironmentError(
                "Linux PNG rendering requires an X11 display; on a server "
                "run the command through 'xvfb-run -a'"
            )
        qt_platform = os.environ.get("QT_QPA_PLATFORM")
        if qt_platform and qt_platform != "xcb":
            raise RenderEnvironmentError(
                "Linux OCCT rendering requires the Qt xcb backend, not "
                f"{qt_platform!r}"
            )
    try:
        import PyQt5  # noqa: F401
    except ImportError as exception:
        raise RenderEnvironmentError(
            "PNG rendering requires the ZenCad GUI dependencies; install "
            "them with 'python -m pip install zencad[gui]'"
        ) from exception


def render_snapshot(
    snapshot,
    output_path,
    *,
    views=("iso",),
    size=(1024, 768),
    display_mode="shaded-with-edges",
    background="#303030",
    axes=False,
    margin=0.07,
) -> RenderResult:
    """Render a managed scene snapshot into one PNG or a contact sheet.

    ``size`` is the size of each view. Multiple views use a deterministic,
    row-major near-square grid in the order supplied by ``views``.
    """
    from zencad.runtime.scene_protocol import SceneSnapshot

    if not isinstance(snapshot, SceneSnapshot):
        raise TypeError("render_snapshot requires a SceneSnapshot")
    normalized_views = parse_views(views)
    tile_width, tile_height = parse_size(size)
    background_rgb = parse_background(background)
    if display_mode not in DISPLAY_MODES:
        raise ValueError(
            "Display mode must be one of {}".format(", ".join(DISPLAY_MODES))
        )
    if not isinstance(axes, bool):
        raise ValueError("Axes must be a boolean")
    if (
        isinstance(margin, bool)
        or not isinstance(margin, (int, float))
        or not math.isfinite(margin)
        or not 0 <= margin < 1
    ):
        raise ValueError("Margin must be a number from 0 up to (but not including) 1")
    if not any(
        record.properties.get("visible", True) for record in snapshot.objects
    ):
        raise EmptySceneError("Scene contains no visible objects")

    destination = Path(output_path).expanduser().resolve()
    if destination.suffix.lower() != ".png":
        raise ValueError("Output path must end in .png")
    _check_render_environment()
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exception:
        raise RenderEnvironmentError(
            f"Could not create output directory {str(destination.parent)!r}: "
            f"{exception}"
        ) from exception
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
        from OCP.Aspect import Aspect_GFM_VER
        from OCP.Quantity import Quantity_Color, Quantity_TOC_sRGB
        from zencad.gui.display import DisplayWidget
    except ImportError as exception:
        raise RenderEnvironmentError(
            "PNG rendering requires the ZenCad GUI dependencies; install "
            "them with 'python -m pip install zencad[gui]'"
        ) from exception

    if threading.current_thread() is not threading.main_thread():
        raise RenderEnvironmentError(
            "Rendering must run on the process main thread"
        )
    application = QtWidgets.QApplication.instance()
    if application is not None and not isinstance(
        application, QtWidgets.QApplication
    ):
        raise RenderEnvironmentError(
            "Rendering requires QApplication, but another Qt application "
            "type already exists"
        )
    owns_application = application is None
    if application is None:
        application = QtWidgets.QApplication([])
    if QtCore.QThread.currentThread() != application.thread():
        raise RenderEnvironmentError("Rendering must run on the Qt application thread")
    quit_on_last_window = application.quitOnLastWindowClosed()
    application.setQuitOnLastWindowClosed(False)

    widget = None
    try:
        widget = DisplayWidget(axis_triedron=bool(axes))
        widget.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        widget.resize(tile_width, tile_height)
        widget.move(-20000, -20000)
        widget.show()
        application.processEvents()
        widget.View.MustBeResized()
        widget.set_msaa_samples(0, redraw=False)
        # Command-line colors are conventional sRGB hex values.  OCCT's
        # Quantity_TOC_RGB input is linear and would turn #303030 into a much
        # lighter framebuffer value, so keep the color space explicit here.
        background_color = Quantity_Color(
            *background_rgb,
            Quantity_TOC_sRGB,
        )
        widget.View.SetBgGradientColors(
            background_color,
            background_color,
            Aspect_GFM_VER,
            True,
        )
        widget.apply_snapshot(snapshot)
        _apply_display_mode(widget, display_mode)
        widget.set_perspective(False)

        orientations = _orientation_values()
        images = []
        with tempfile.TemporaryDirectory(prefix="zencad-preview-") as temporary:
            temporary_path = Path(temporary)
            for index, view_name in enumerate(normalized_views):
                widget.View.SetProj(orientations[view_name], False)
                widget.View.FitAll(float(margin), False)
                widget.View.Redraw()
                application.processEvents()
                tile_path = temporary_path / f"view-{index}.png"
                if not widget.View.Dump(str(tile_path)):
                    raise RenderEnvironmentError(
                        f"OCCT could not render the {view_name!r} view"
                    )
                image = QtGui.QImage(str(tile_path))
                if image.isNull():
                    raise RenderEnvironmentError(
                        f"OCCT produced an unreadable {view_name!r} image"
                    )
                if image.size() != QtCore.QSize(tile_width, tile_height):
                    image = image.scaled(
                        tile_width,
                        tile_height,
                        QtCore.Qt.IgnoreAspectRatio,
                        QtCore.Qt.SmoothTransformation,
                    )
                images.append(image)

            columns, rows = contact_sheet_grid(len(images))
            sheet = QtGui.QImage(
                columns * tile_width,
                rows * tile_height,
                QtGui.QImage.Format_RGB32,
            )
            red, green, blue = (
                round(channel * 255) for channel in background_rgb
            )
            sheet.fill(QtGui.QColor(red, green, blue))
            painter = QtGui.QPainter(sheet)
            try:
                for index, image in enumerate(images):
                    painter.drawImage(
                        (index % columns) * tile_width,
                        (index // columns) * tile_height,
                        image,
                    )
            finally:
                painter.end()

            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.stem}.",
                suffix=".png",
                dir=destination.parent,
            )
            os.close(descriptor)
            temporary_output = Path(temporary_name)
            try:
                if not sheet.save(str(temporary_output), "PNG"):
                    raise RenderEnvironmentError(
                        f"Qt could not encode {destination.name!r} as PNG"
                    )
                os.replace(temporary_output, destination)
            finally:
                temporary_output.unlink(missing_ok=True)
    except RenderError:
        raise
    except Exception as exception:
        raise RenderEnvironmentError(
            f"Native preview rendering failed: {exception}"
        ) from exception
    finally:
        if widget is not None:
            widget.close()
            application.processEvents()
        application.setQuitOnLastWindowClosed(quit_on_last_window)
        if owns_application:
            application.quit()

    columns, rows = contact_sheet_grid(len(normalized_views))
    return RenderResult(
        path=destination,
        views=normalized_views,
        tile_size=(tile_width, tile_height),
        image_size=(columns * tile_width, rows * tile_height),
    )


def render_script(
    script_path,
    output_path,
    *,
    views=("iso",),
    size=(1024, 768),
    display_mode="shaded-with-edges",
    background="#303030",
    axes=False,
    margin=0.07,
    timeout=30,
    arguments=(),
    output: Callable[[str, str], None] | None = None,
) -> RenderResult:
    """Evaluate a ZenCad script in isolation and render its final scene."""
    script = Path(script_path).expanduser().resolve()
    if not script.is_file():
        raise FileNotFoundError(script)
    _check_render_environment()
    snapshot = _evaluate_script(script, list(arguments), float(timeout), output)
    return render_snapshot(
        snapshot,
        output_path,
        views=views,
        size=size,
        display_mode=display_mode,
        background=background,
        axes=axes,
        margin=margin,
    )


def _argument_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="zencad render",
        description="Render a deterministic PNG preview without opening the editor.",
    )
    parser.add_argument("script", help="ZenCad Python script")
    parser.add_argument("-o", "--output", required=True, help="output PNG path")
    parser.add_argument(
        "--view", "--views",
        dest="views",
        action="append",
        help="fixed view; repeat or use commas (default: iso)",
    )
    parser.add_argument(
        "--size",
        default="1024x768",
        metavar="WIDTHxHEIGHT",
        help="size of each view in pixels (default: 1024x768)",
    )
    parser.add_argument(
        "--mode",
        choices=DISPLAY_MODES,
        default="shaded-with-edges",
        help="presentation mode (default: shaded-with-edges)",
    )
    parser.add_argument(
        "--background",
        default="#303030",
        metavar="#RRGGBB",
        help="solid background color (default: #303030)",
    )
    parser.add_argument("--axes", action="store_true", help="show XYZ axes")
    parser.add_argument(
        "--margin",
        type=float,
        default=0.07,
        help="FitAll margin from 0 up to 1 (default: 0.07)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="script evaluation timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "script_arguments",
        nargs="*",
        help="arguments passed to the model script (put them after --)",
    )
    return parser


def render_cli(argv=None):
    """Command-line adapter. Returns a process exit code."""
    parser = _argument_parser()
    arguments = parser.parse_args(argv)
    try:
        views = parse_views(arguments.views or ("iso",))
        size = parse_size(arguments.size)
        background = parse_background(arguments.background)
        result = render_script(
            arguments.script,
            arguments.output,
            views=views,
            size=size,
            display_mode=arguments.mode,
            background=background,
            axes=arguments.axes,
            margin=arguments.margin,
            timeout=arguments.timeout,
            arguments=arguments.script_arguments,
            output=lambda stream, text: print(
                text,
                end="",
                file=sys.stdout if stream == "stdout" else sys.stderr,
            ),
        )
    except (ValueError, FileNotFoundError) as exception:
        parser.error(str(exception))
    except EmptySceneError as exception:
        print(f"zencad render: {exception}", file=sys.stderr)
        return 4
    except RenderScriptError as exception:
        print(f"zencad render: {exception}", file=sys.stderr)
        return 3
    except RenderTimeoutError as exception:
        print(f"zencad render: {exception}", file=sys.stderr)
        return 5
    except RenderEnvironmentError as exception:
        print(f"zencad render: {exception}", file=sys.stderr)
        return 6
    print(result.path)
    return 0


__all__ = [
    "DISPLAY_MODES",
    "VIEW_NAMES",
    "EmptySceneError",
    "RenderEnvironmentError",
    "RenderError",
    "RenderResult",
    "RenderScriptError",
    "RenderTimeoutError",
    "contact_sheet_grid",
    "parse_background",
    "parse_size",
    "parse_views",
    "render_script",
    "render_snapshot",
]
