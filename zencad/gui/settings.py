#!/usr/bin/env python3

from PyQt5.QtCore import *

class Settings():
	list_of_settings = {
			"gui" : {
			"text_editor" : "subl"
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


if __name__ == "__main__":
	settings = Settings()
	settings.restore()

	print(settings.list_of_settings)



