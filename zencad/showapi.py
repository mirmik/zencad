from pyservoce import Scene, Color
import argparse
import evalcache
import sys

default_scene = Scene()
mode = None

def display(shp, color = Color(0.6, 0.6, 0.8)):
	if isinstance(shp, evalcache.LazyObject):
		return default_scene.add(evalcache.unlazy(shp), color)
	else:
		return default_scene.add(shp, color)

def disp(*args,**kwargs): return display(*args, **kwargs)

def highlight(m): return display(m, Color(0.5, 0, 0, 0.5))
def hl(m) : return highlight(m)

def show(scene=None, sargv=sys.argv[1:], *args, **kwargs):
	if scene is None: scene = default_scene

	if mode is not None:		
		if mode == "nothing":
			pass

		elif mode == "update_scene":
			import zencad.shower
			return zencad.shower.update_scene(scene, *args, **kwargs)


		elif mode == "app_fullview":
			import zencad.shower
			return zencad.shower.show_impl(scene, *args, showeditor=True, showconsole=True, **kwargs)

	else:
		import zencad.shower
		return zencad.shower.show_impl(scene, *args, **kwargs)