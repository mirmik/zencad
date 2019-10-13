from pyservoce import Scene, Color
import argparse
import evalcache
import sys

import zencad.assemble
import zencad.gui.application

default_scene = Scene()
SHOWMODE = "makeapp"
PRESCALE = False
SLEEPED = False
SESSION_ID = 0
EXECPATH = sys.argv[0]

def show(scene=None, *args, sargv=sys.argv[1:], standalone=False, **kwargs):
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
        scene = default_scene

    if SHOWMODE == "makeapp":
        # Common application start
        zencad.gui.application.start_unbound_application(
            scene=scene, *args, tgtpath=EXECPATH, **kwargs)

    elif SHOWMODE == "widget":
        # Start widget without main programm
        zencad.gui.viewadaptor.standalone(scene=scene, *args, **kwargs)

    elif SHOWMODE == "replace":
        # Replace main programm widget with target id's widget
        zencad.gui.application.update_unbound_application(
            scene=scene, need_prescale=PRESCALE, sleeped=SLEEPED, session_id=SESSION_ID, *args, **kwargs)

    elif SHOWMODE == "noshow":
        return

    else:
        raise Exception("undeclared SHOWMODE")

def display(shp, color=Color(0.6, 0.6, 0.8), deep=True):
    if isinstance(shp, evalcache.LazyObject):
        shp = evalcache.unlazy(shp)

    if isinstance(shp, zencad.assemble.unit):
        return shp.bind_scene(default_scene, color=color, deep=deep)

    return default_scene.add(shp, color)


def disp(*args, **kwargs):
    return display(*args, **kwargs)


def highlight(m):
    display(m, Color(0.5, 0, 0, 0.5))
    return m


def hl(m):
    return highlight(m)
