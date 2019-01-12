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

def disp(*args,**kwargs): display(*args, **kwargs)

def highlight(m): return display(m, Color(0.5, 0, 0, 0.5))
def hl(m) : return highlight(m)

def show(scene=None, shower="app_prototype", sargv=sys.argv[1:], *args, **kwargs):
	if scene is None: scene = default_scene

	if mode is not None:
		if mode == "view":
			import zencad.unbound
			zencad.viewadapter.start_self(scene, *args, **kwargs)
			
		elif mode == "viewadapter":
			pass

		return

	parser = argparse.ArgumentParser(description='zen')
	parser.add_argument("--v1", action='store_true')
	parser.add_argument("--view", action='store_true')

	sargv = parser.parse_args(sargv)	

	if sargv.v1:
		shower = "app_v1"

	elif sargv.view:
		shower = "viewonly"
	
	if shower == "app_prototype":
		import zencad.shower
		return zencad.shower.show_impl(scene, *args, **kwargs)

	elif shower == "app_v1":
		import zencad.unbound
		zencad.unbound.start_unbound(scene, *args, **kwargs)

	elif shower == "viewonly":
		import zencad.unbound
		zencad.viewadapter.start_self(scene, *args, **kwargs)