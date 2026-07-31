#!/usr/bin/env python3
"""ZenCad settings with lazy Qt persistence.

Geometry imports use the defaults below and do not require PyQt.  The GUI
loads QSettings only when settings are explicitly restored or stored.
"""

import os
import sys


def default_text_editor_os():
    if sys.platform == "linux":
        return "xdg-open {path}"
    if sys.platform in ("win32", "win64"):
        return "notepad.exe {path}"
    return ""


class ZencadSettings:
    def __init__(self):
        self.list_of_settings = {
            "gui": {
                "text_editor": default_text_editor_os(),
                "start_widget": True,
                "bind_widget": True,
            },
            "view": {
                "default_color": (0.6, 0.6, 0.8, 0),
                "default_chordial_deviation": 0.1,
            },
            "memory": {
                "recents": [],
                "hsplitter_position": (300, 500),
                "vsplitter_position": (500, 300),
                "console_hidden": False,
                "texteditor_hidden": False,
                "wsize": None,
            },
            "markers": {"size": 1},
        }
        self.restored = False

    def restore(self):
        if self.restored:
            return
        try:
            from PyQt5.QtCore import QSettings
        except ImportError:
            self.restored = True
            return

        settings = QSettings("ZenCad", "settings")
        for group, values in self.list_of_settings.items():
            settings.beginGroup(group)
            for key, default in values.items():
                values[key] = settings.value(key, default)
            settings.endGroup()
        self.restored = True

    def store(self):
        from PyQt5.QtCore import QSettings

        settings = QSettings("ZenCad", "settings")
        for group, values in self.list_of_settings.items():
            settings.beginGroup(group)
            for key, value in values.items():
                settings.setValue(key, value)
            settings.endGroup()

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
