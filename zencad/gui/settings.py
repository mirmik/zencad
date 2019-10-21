from PyQt5.QtCore import *

list_of_settings = {
	"text_editor" : "subl",
	"recent" : []	
}

class Settings(QSettings):
	def __init__(self):

