#!/usr/bin/env python3
"""Qt-independent ZenCad settings persistence."""

import configparser
import io
import json
import os
from pathlib import Path
import pickle
import re
import sys
import tempfile


MSAA_SAMPLE_OPTIONS = (0, 2, 4, 8)
DEFAULT_MSAA_SAMPLES = 4


def normalize_msaa_samples(value):
    try:
        samples = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MSAA_SAMPLES
    if samples not in MSAA_SAMPLE_OPTIONS:
        return DEFAULT_MSAA_SAMPLES
    return samples


def default_text_editor_os():
    if sys.platform == "linux":
        return "xdg-open {path}"
    if sys.platform in ("win32", "win64"):
        return "notepad.exe {path}"
    return ""


def default_settings_path():
    """Return the per-user settings file without importing a GUI toolkit."""
    if sys.platform in ("win32", "win64"):
        root = Path(os.environ.get(
            "APPDATA",
            Path.home() / "AppData" / "Roaming",
        ))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get(
            "XDG_CONFIG_HOME",
            Path.home() / ".config",
        ))
    return root / "ZenCad" / "settings.conf"


class _PrimitiveUnpickler(pickle.Unpickler):
    """Read legacy QSettings primitive variants without loading classes."""

    def find_class(self, module, name):
        raise pickle.UnpicklingError(
            f"global {module}.{name} is not allowed in settings"
        )

    def persistent_load(self, pid):
        raise pickle.UnpicklingError(
            "persistent objects are not allowed in settings"
        )


def _decode_qsettings_bytes(value):
    """Decode the byte escaping used by QSettings INI variant values."""
    result = bytearray()
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            result.extend(char.encode("utf-8"))
            index += 1
            continue

        index += 1
        if index >= len(value):
            result.append(ord("\\"))
            break
        escape = value[index]
        if escape == "0":
            result.append(0)
            index += 1
        elif escape == "x":
            index += 1
            match = re.match(r"[0-9a-fA-F]{1,2}", value[index:])
            if match is None:
                result.extend(b"\\x")
            else:
                result.append(int(match.group(0), 16))
                index += len(match.group(0))
        else:
            result.extend(escape.encode("utf-8"))
            index += 1
    return bytes(result)


def _decode_qsettings_variant(value):
    try:
        payload = _decode_qsettings_bytes(value)
        pickle_start = payload.index(b"\x80")
        decoded = _PrimitiveUnpickler(
            io.BytesIO(payload[pickle_start:])
        ).load()
    except (ValueError, pickle.PickleError, EOFError):
        return None
    if decoded is None or isinstance(
        decoded,
        (bool, int, float, str, list, tuple, dict),
    ):
        return decoded
    return None


def _decode_legacy_value(value, default):
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False

    if value.startswith("@Rect(") and value.endswith(")"):
        try:
            return [int(item) for item in value[6:-1].split()]
        except ValueError:
            return default

    if value.startswith("@Variant(") and value.endswith(")"):
        decoded = _decode_qsettings_variant(value[9:-1])
        return default if decoded is None else decoded

    if isinstance(default, str):
        return value
    if isinstance(default, bool):
        return lower == "true"
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    if isinstance(default, float):
        try:
            return float(value)
        except ValueError:
            return default
    if isinstance(default, (list, tuple)):
        if not value:
            return []
        values = [item.strip() for item in value.split(",")]
        if default and all(isinstance(item, int) for item in default):
            try:
                return [int(item) for item in values]
            except ValueError:
                return default
        if default and all(isinstance(item, (int, float)) for item in default):
            try:
                return [float(item) for item in values]
            except ValueError:
                return default
        return values
    if default is None and lower in ("", "none", "null"):
        return None
    return value


def _decode_value(value, default):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return _decode_legacy_value(value, default)


def _serializable_value(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serializable_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _serializable_value(item)
            for key, item in value.items()
        }

    rect_accessors = ("x", "y", "width", "height")
    if all(callable(getattr(value, name, None)) for name in rect_accessors):
        return [int(getattr(value, name)()) for name in rect_accessors]
    raise TypeError(f"Unsupported settings value: {type(value).__name__}")


class ZencadSettings:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_settings_path()
        self.list_of_settings = {
            "gui": {
                "text_editor": default_text_editor_os(),
            },
            "view": {
                "default_color": (0.6, 0.6, 0.8, 0),
                "default_chordial_deviation": 0.1,
                "msaa_samples": DEFAULT_MSAA_SAMPLES,
                "navigation_scheme": "zencad",
                "navigation_rotate": "left",
                "navigation_pan": "middle",
                "navigation_zoom": "none",
                "navigation_invert_wheel": False,
                "navigation_invert_orbit": False,
            },
            "memory": {
                "recents": [],
                "hsplitter_position": (430, 670),
                "vsplitter_position": (540, 180),
                "console_hidden": False,
                "texteditor_hidden": False,
                "wsize": None,
            },
            "markers": {"size": 1},
        }
        self.restored = False

    @staticmethod
    def _new_parser():
        return configparser.ConfigParser(interpolation=None)

    def _read_parser(self):
        parser = self._new_parser()
        try:
            with self.path.open(encoding="utf-8") as stream:
                parser.read_file(stream)
        except FileNotFoundError:
            pass
        return parser

    def restore(self):
        if self.restored:
            return
        try:
            parser = self._read_parser()
        except (OSError, configparser.Error):
            self.restored = True
            return

        for group, values in self.list_of_settings.items():
            if not parser.has_section(group):
                continue
            for key, default in values.items():
                if parser.has_option(group, key):
                    values[key] = _decode_value(
                        parser.get(group, key, raw=True),
                        default,
                    )
        self.restored = True

    def store(self):
        parser = self._read_parser()
        for group, values in self.list_of_settings.items():
            if not parser.has_section(group):
                parser.add_section(group)
            for key, value in values.items():
                parser.set(
                    group,
                    key,
                    json.dumps(
                        _serializable_value(value),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            dir=self.path.parent,
            text=True,
        )
        try:
            with os.fdopen(
                file_descriptor,
                "w",
                encoding="utf-8",
            ) as stream:
                parser.write(stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.path)
        finally:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass

    @staticmethod
    def _restore_type(value):
        if value == "true":
            return True
        if value == "false":
            return False
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                pass
        return value

    def get(self, path):
        value = self.list_of_settings
        for component in path:
            value = value[component]
        return self._restore_type(value)

    def set(self, path, value):
        target = self.list_of_settings
        for component in path[:-1]:
            target = target[component]
        target[path[-1]] = value

    def get_recent(self):
        recents = self.list_of_settings["memory"]["recents"] or []
        if isinstance(recents, str):
            recents = [recents]
        self.list_of_settings["memory"]["recents"] = recents
        self.clear_deleted_recent()
        return recents

    def add_recent(self, added):
        recents = self.get_recent()
        while added in recents:
            recents.remove(added)
        recents.insert(0, added)
        del recents[10:]
        self.store()

    def clear_deleted_recent(self):
        recents = self.list_of_settings["memory"]["recents"]
        existing = [path for path in recents if os.path.isfile(path)]
        if existing != recents:
            self.list_of_settings["memory"]["recents"] = existing
            self.store()


Settings = ZencadSettings()


if __name__ == "__main__":
    Settings.restore()
    print(Settings.list_of_settings)
