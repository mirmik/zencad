from pyservoce import Scene, Color
import argparse
import evalcache
import sys

import zencad.assemble
import zencad.unbound.application

default_scene = Scene()
SHOWMODE = "makeapp"

def display(shp, color=Color(0.6, 0.6, 0.8), deep=True):
    if isinstance(shp, evalcache.LazyObject):
        shp = evalcache.unlazy(shp)

    if isinstance(shp, zencad.assemble.unit):
        return shp.bind_scene(default_scene, color=color, deep=deep)

    return default_scene.add(shp, color)


def disp(*args, **kwargs):
    return display(*args, **kwargs)


def highlight(m):
    return display(m, Color(0.5, 0, 0, 0.5))


def hl(m):
    return highlight(m)


def show(scene=None, sargv=sys.argv[1:], *args, **kwargs):
    if scene is None:
        scene = default_scene

    if SHOWMODE == "makeapp":
        zencad.unbound.application.start_unbound_application(scene)

    if SHOWMODE == "mainonly":
        zencad.unbound.application.start_main_application()

    elif SHOWMODE == "widget":
        zencad.viewadaptor.standalone(scene)

    elif SHOWMODE == "replace":
        zencad.unbound.application.update_unbound_application(scene)

    #if mode is not None:
    #   if mode == "nothing":
    #        pass
#
    #    elif mode == "update_scene":
    #        import zencad.shower
#
    #        return zencad.shower.update_scene(scene, *args, **kwargs)
#
    #    elif mode == "app_fullview":
    #        import zencad.shower
#
    #        return zencad.shower.show_impl(
    #            scene, *args, showeditor=True, showconsole=True, **kwargs
    #        )
#
    #else:
    #    import zencad.shower
#
    #    return zencad.shower.show_impl(scene, *args, **kwargs)
