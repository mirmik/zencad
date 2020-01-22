#!/usr/bin/env python3

from PyQt5.QtCore import *
import pyservoce
import sys

restored = False
pre_default_color = (0.6, 0.6, 0.8, 0)

def default_text_editor_os():
	if sys.platform == "linux":
		return "xdg-open {path}"
	elif sys.platform in ["win32", "win64"]:
		return "notepad.exe {path}"
	else:
		return "" 

class Settings():
	list_of_settings = {
		"gui" : {
			"text_editor" : default_text_editor_os(),
			"start_widget" : True,
			"bind_widget" : True
		},
		"view" : {
			"default_color_red" : pre_default_color[0],
			"default_color_green" : pre_default_color[1],
			"default_color_blue" : pre_default_color[2],
			"default_color_alpha" : pre_default_color[3],
		},
		"memory" : {
			"recents" : [],
			"hsplitter_position": None,
			"vsplitter_position": None,
			"wsize": None
		}
	}
	
	#def __init__(self):
	#	super().__init__()

	@classmethod
	def store(self):
		settings = QSettings("ZenCad", "settings")

		for g in self.list_of_settings:
			settings.beginGroup(g)
			for k in self.list_of_settings[g]:
				settings.setValue(k, self.list_of_settings[g][k])
			settings.endGroup()

	@classmethod
	def restore(self):
		global restored

		if restored:
			return

		settings = QSettings("ZenCad", "settings")

		for g in self.list_of_settings:
			settings.beginGroup(g)
			for k in self.list_of_settings[g]:
				self.list_of_settings[g][k] = settings.value(k, self.list_of_settings[g][k])
			settings.endGroup()

		restored = True

	@classmethod
	def set_editor(self, editor):
		self.list_of_settings["gui"]["text_editor"] = editor
		self.store()

	@classmethod
	def set_default_color(self, r, g, b, a):
		self.list_of_settings["view"]["default_color_red"] = r
		self.list_of_settings["view"]["default_color_green"] = g
		self.list_of_settings["view"]["default_color_blue"] = b
		self.list_of_settings["view"]["default_color_alpha"] = a
		self.store()

	@classmethod
	def get_default_color(self):
		return (
			float(self.list_of_settings["view"]["default_color_red"]),
			float(self.list_of_settings["view"]["default_color_green"]),
			float(self.list_of_settings["view"]["default_color_blue"]),
			float(self.list_of_settings["view"]["default_color_alpha"])
		)

	@classmethod
	def add_recent(self, added):
		while added in self.list_of_settings["memory"]["recents"]: 
			self.list_of_settings["memory"]["recents"].remove(added)

		self.list_of_settings["memory"]["recents"] = [ added ] + self.list_of_settings["memory"]["recents"]
		if len(self.list_of_settings["memory"]["recents"]) > 10:
			self.list_of_settings["memory"]["recents"] = self.list_of_settings["memory"]["recents"][:10]

		self.store()

	@classmethod
	def get_recent(self):
		return self.list_of_settings["memory"]["recents"]

	@classmethod
	def get_settings(self):
		return self.list_of_settings


Settings.restore()

def restore():
	Settings.restore()

def hsplitter_position_get():
	return Settings.list_of_settings["memory"]["hsplitter_position"]

def vsplitter_position_get():
	return Settings.list_of_settings["memory"]["vsplitter_position"]
	
def get(path):
	it = Settings.list_of_settings
	for p in path:
		it = it[p]
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



