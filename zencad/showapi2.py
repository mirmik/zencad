from scene import Scene

__default_scene = Scene()

def display(shp, color=None, deep=True, scene=None):
	if scene is None:
		scene = __default_scene

	__default_scene.add(shp, color)

def disp(*args, **kwargs):
	return display(*args, **kwargs)

def show(scene=None, display_only=False):
	if scene is None:
		scene = __default_scene

	if display_only:
		import gui.display_only
		gui.display_only.init_display_only_mode()
		gui.display_only.DISPLAY.attach_scene(scene)
		gui.display_only.exec_display_only_mode()
