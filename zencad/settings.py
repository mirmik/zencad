#!/usr/bin/env python3
import os

from PyQt5.QtCore import *
import pyservoce
import sys


def default_text_editor_os():
    if sys.platform == "linux":
        return "xdg-open {path}"
    elif sys.platform in ["win32", "win64"]:
        return "notepad.exe {path}"
    else:
        return ""

class BaseSettings:
    def __init__(self, name, subname, default):
        self.name = name
        self.subname = subname  
        self.list_of_settings = default
        self.restored=False

    def store(self):
        settings = QSettings(self.name, self.subname)

        for g in self.list_of_settings:
            settings.beginGroup(g)
            for k in self.list_of_settings[g]:
                settings.setValue(k, self.list_of_settings[g][k])
            settings.endGroup()

    def restore(self):
        global restored

        if self.restored:
            return

        settings = QSettings(self.name, self.subname)

        for g in self.list_of_settings:
            settings.beginGroup(g)
            for k in self.list_of_settings[g]:
                self.list_of_settings[g][k] = settings.value(
                    k, self.list_of_settings[g][k])
            settings.endGroup()

        restored = True

class ZencadSettings(BaseSettings):
    def __init__(self):
        list_of_settings = {
            "gui": {
                "text_editor": default_text_editor_os(),
                "start_widget": True,
                "bind_widget": True
            },
            "view": {
                "default_color": (0.6, 0.6, 0.8, 0),
                "default_chordial_deviation": 0.003
            },
            "memory": {
                "recents": [],
                "hsplitter_position": (300, 500),
                "vsplitter_position": (500, 300),
                "console_hidden": False,
                "texteditor_hidden": False,
                "wsize": (640,480),
                "perspective": False
            },
            "markers": {
                "size": 1
            }
        }

        super().__init__("ZenCad", "settings", list_of_settings)

    def set_editor(self, editor):
        self.list_of_settings["gui"]["text_editor"] = editor
        self.store()

    def set_default_color(self, r, g, b, a):
        self.list_of_settings["view"]["default_color_red"] = r
        self.list_of_settings["view"]["default_color_green"] = g
        self.list_of_settings["view"]["default_color_blue"] = b
        self.list_of_settings["view"]["default_color_alpha"] = a
        self.store()

    def get_default_color(self):
        return (
            float(self.list_of_settings["view"]["default_color_red"]),
            float(self.list_of_settings["view"]["default_color_green"]),
            float(self.list_of_settings["view"]["default_color_blue"]),
            float(self.list_of_settings["view"]["default_color_alpha"])
        )

    def add_recent(self, added):
        while added in self.list_of_settings["memory"]["recents"]:
            self.list_of_settings["memory"]["recents"].remove(added)

        self.list_of_settings["memory"]["recents"] = [
            added] + self.list_of_settings["memory"]["recents"]
        if len(self.list_of_settings["memory"]["recents"]) > 10:
            self.list_of_settings["memory"]["recents"] = self.list_of_settings["memory"]["recents"][:10]

        self.store()

    def clear_deleted_recent(self):
        recents = self.list_of_settings["memory"]["recents"]
        need_store = False

        for r in recents:
            if not os.path.exists(r) or not os.path.isfile(r):
                self.list_of_settings["memory"]["recents"].remove(r)
                need_store = True

        if need_store:
            self.store()

    def get_recent(self):
        # Перестраховка.
        if self.list_of_settings["memory"]["recents"] is None:
            self.list_of_settings["memory"]["recents"] = []

        self.clear_deleted_recent()
        return self.list_of_settings["memory"]["recents"]

    def get_settings(self):
        return self.list_of_settings


    def _restore_type(self, val):
        if val == "true":
            return True
        if val == "false":
            return False

        if isinstance(val, str):
            try:
                if float(val):
                    return float(val)
            except:
                pass

        return val

    def get(self, path):
        it = self.list_of_settings
        for p in path:
            it = it[p]

        it = self._restore_type(it)
        return it

Settings = ZencadSettings()
Settings.restore()


def restore():
    Settings.restore()


def hsplitter_position_get():
    return Settings.list_of_settings["memory"]["hsplitter_position"]


def vsplitter_position_get():
    return Settings.list_of_settings["memory"]["vsplitter_position"]


def _restore_type(val):
    if val == "true":
        return True
    if val == "false":
        return False

    if isinstance(val, str):
        try:
            if float(val):
                return float(val)
        except:
            pass

    return val


def get(path):
    it = Settings.list_of_settings
    for p in path:
        it = it[p]

    it = _restore_type(it)
    return it


def set(path, value):
    it = Settings.list_of_settings
    for p in path[:-1]:
        it = it[p]
    it[path[-1]] = value


def store():
    Settings.store()


def get_default_color():
    return Settings.get_default_color()


def get_external_editor_command():
    return Settings.list_of_settings["gui"]["text_editor"]


def list():
    return Settings.list_of_settings


def start_screen(en):
    Settings.list_of_settings["gui"]["start_widget"] = "false" if en else "true"
    store()


if __name__ == "__main__":
    print(Settings.list_of_settings)
