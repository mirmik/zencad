#!/usr/bin/env python3

from PyQt5.QtCore import *
import pyservoce

default_color = (0.6, 0.6, 0.8, 0)

class Settings():
	list_of_settings = {
		"gui" : {
			"text_editor" : "subl",
		},
		"view" : {
			"default_color_red" : default_color[0],
			"default_color_green" : default_color[1],
			"default_color_blue" : default_color[2],
			"default_color_alpha" : default_color[3],
		},
		"memory" : {
			"recents" : []
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
		settings = QSettings("ZenCad", "settings")

		for g in self.list_of_settings:
			settings.beginGroup(g)
			for k in self.list_of_settings[g]:
				self.list_of_settings[g][k] = settings.value(k, self.list_of_settings[g][k])
			settings.endGroup()

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

if __name__ == "__main__":
	print(Settings.list_of_settings)



