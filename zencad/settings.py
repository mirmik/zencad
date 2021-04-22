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
                "default_chordial_deviation": 0.1
            },
            "memory": {
                "recents": [],
                "hsplitter_position": (300, 500),
                "vsplitter_position": (500, 300),
                "console_hidden": False,
                "texteditor_hidden": False,
                "wsize": None
            },
            "markers": {
                "size": 1
            }
        }

        super().__init__("ZenCad", "settings", list_of_settings)


Settings = ZencadSettings()
Settings.restore()

if __name__ == "__main__":
    print(Settings.list_of_settings)
