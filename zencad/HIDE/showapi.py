from pyservoce import Scene, Color
import pyservoce
import argparse
import evalcache
import sys

import zencad.assemble
import zencad.gui.application

__default_scene = None
def default_scene():
    global __default_scene
    if __default_scene is None:
        __default_scene = Scene()
        __default_scene.set_chordial_deviation(False, zencad.settings.get(["view", "default_chordial_deviation"]))
    return __default_scene

#__default_view = None
#def default_view():
#    global __default_view
#    if __default_view is None:
#        __default_view = default_scene.viewer.create_view()
#        __default_view.set_triedron()
#        __default_view.set_gradient(pyservoce.color(0.5,0.5,0.5), pyservoce.color(0.3,0.3,0.3))
#    return __default_view

SHOWMODE = "makeapp"
PRESCALE = False
SLEEPED = False
SESSION_ID = 0
SIZE = (640,480)
EXECPATH = sys.argv[0]

def show(scene=None, *args, sargv=sys.argv[1:], standalone=False, debug=False, **kwargs):
    """ Функция активации графической части.

    Может иметь разные режимы исполнения в зависимости от текущего
    режима. Обычно или создаёт GUI либо заменяет в виджет в уже 
    созданном приложении.
    """
    global SHOWMODE

    if "-c" in sys.argv:
        print("Sorry. ZenCad Gui support python interactive mode for standalone widget mode only.") 
        print("Now I have to recommend not using interactive mode.")
        print("Please use script or `zencad` entry point if you need normal gui.") 
        SHOWMODE = "widget"

    if standalone:
        SHOWMODE = "widget"

    if scene is None:
        scene = default_scene()

    if SHOWMODE == "makeapp":
        # Common application start
        zencad.gui.application.start_unbound_application(
            scene=scene, *args, tgtpath=EXECPATH, debug=debug, **kwargs)

    elif SHOWMODE == "widget":
        # Start widget without main programm
        zencad.gui.viewadaptor.standalone(scene=scene, *args, **kwargs)

    elif SHOWMODE == "replace":
        # Replace main programm widget with target id's widget
        zencad.gui.application.update_unbound_application(
            scene=scene, need_prescale=PRESCALE, sleeped=SLEEPED, session_id=SESSION_ID, size=SIZE, *args, **kwargs)

    elif SHOWMODE == "noshow":
        print("showapi: showing disabled")
        return

    else:
        raise Exception("undeclared SHOWMODE")

default_color = zencad.settings.Settings.get_default_color()

class stub_controller:
    def __init__(self, shp):
        self.shp = shp

    def hide(self, en):
        pass


def display(shp, color=None, deep=True, scene=None):
    if scene is None:
        scene = default_scene()

    if default_scene() is None:
        # TODO: Add another stubs
        if isinstance(shp, evalcache.LazyObject):
            return stub_controller(shp.unlazy())
        else:
            return stub_controller(shp)    

    if isinstance(shp, evalcache.LazyObject):
        shp = evalcache.unlazy(shp)

    if isinstance(shp, list) or isinstance(shp, tuple):
        lst = []
        for s in shp:
            lst.append(display(s, color=color, deep=deep, scene=scene))

        return lst

    if isinstance(shp, zencad.assemble.unit):
        return shp.bind_scene(scene, color=color, deep=deep)

    if color is None:
        color=default_color
        
    if scene is None:
        return pyservoce.interactive_object(shp, color)

    return scene.add(shp, color)


def disp(*args, **kwargs):
    return display(*args, **kwargs)


def highlight(m, color=Color(0.5, 0, 0, 0.5)):
    display(m, color)
    return m


def hl(m):
    return highlight(m)
