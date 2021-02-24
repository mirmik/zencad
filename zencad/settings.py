#!/usr/bin/env python3
import os
import sys

from PyQt5.QtCore import *
from zenframe.settings import BaseSettings, default_text_editor_os


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
                "wsize": (640, 480)
            },
            "markers": {
                "size": 1
            }
        }

        super().__init__("ZenCad", "settings", list_of_settings)

    def get_recent(self):
        if self.list_of_settings["memory"]["recents"] is None:
            self.list_of_settings["memory"]["recents"] = []

        self.clear_deleted_recent()
        return self.list_of_settings["memory"]["recents"]

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


Settings = ZencadSettings()
Settings.restore()

if __name__ == "__main__":
    print(Settings.list_of_settings)
