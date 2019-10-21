#!/usr/bin/env python3

from PyQt5.QtCore import *

class Settings():
	list_of_settings = {
		"gui" : {
			"text_editor" : "subl",
		},
		"view" : {
			"default_color_red" : 0.6,
			"default_color_green" : 0.6,
			"default_color_blue" : 0.6,
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
	def set_default_color(self, r, g, b):
		self.list_of_settings["view"]["default_color_red"] = r
		self.list_of_settings["view"]["default_color_red"] = g
		self.list_of_settings["view"]["default_color_red"] = b

	@classmethod
	def get_default_color(self, r, g, b):
		return (
			self.list_of_settings["view"]["default_color_red"],
			self.list_of_settings["view"]["default_color_red"],
			self.list_of_settings["view"]["default_color_red"]
		)


if __name__ == "__main__":
	settings = Settings()
	settings.restore()

	print(settings.list_of_settings)



