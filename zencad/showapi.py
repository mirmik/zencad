from pyservoce import Scene, Color
import argparse
import evalcache
import sys

import zencad.assemble
import zencad.unbound.application

default_scene = Scene()
SHOWMODE = "makeapp"

def show(scene=None, sargv=sys.argv[1:], *args, **kwargs):
    """ Функция активации графической части.

    Может иметь разные режимы исполнения в зависимости от текущего
    режима. Обычно или создаёт GUI либо заменяет в виджет в уже 
    созданном приложении.
    """

    if scene is None:
        scene = default_scene

    if SHOWMODE == "makeapp":
        # Common application start
        zencad.unbound.application.start_unbound_application(
            scene, *args, **kwargs)

    if SHOWMODE == "mainonly":
        # Make mainwindow without widget
        zencad.unbound.application.start_main_application()

    elif SHOWMODE == "widget":
        # Start widget without main programm
        zencad.viewadaptor.standalone(scene)

    elif SHOWMODE == "replace":
        # Replace main programm widget with target id's widget
        zencad.unbound.application.update_unbound_application(
            scene, *args, **kwargs)

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
