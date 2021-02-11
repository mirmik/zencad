#!/usr/bin/env python3

from interactive_object import InteractiveObject
from interactive_object import ShapeInteractiveObject
from interactive_object import create_interactive_object

from axis               import Axis
from shape              import Shape

import evalcache

class Scene:
	def __init__(self):
		self.objects = []
		self.interactives = []
		self.display = None

	def add(self, obj, color=None):
		if isinstance(obj, evalcache.lazy.LazyObject):
			obj = obj.unlazy()

		if isinstance(obj, (Shape,Axis)):
			iobj = create_interactive_object(obj, color)
			self.add_interactive_object(iobj)
		
		elif isinstance(obj, InteractiveObject):
			iobj = obj
			self.add_interactive_object(iobj)

		else:
			raise Exception(f"Unresolved object type, __class__:{obj.__class__}")

		return iobj

	def add_interactive_object(self, iobj):
		self.interactives.append(iobj)
		
		if self.display is not None:
			self.display.display_interactive_object(iobj)