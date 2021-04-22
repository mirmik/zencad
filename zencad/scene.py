#!/usr/bin/env python3

import evalcache

from zencad.interactive import *

from zencad.axis import Axis
from zencad.geom.shape import Shape, LazyObjectShape
from zencad.util import to_Vertex, to_GeomPoint
from zencad.color import default_color
from zencad.interactive import create_interactive_object

import OCC.Core

import numpy


class Scene:
    """Коллекция интерактивных объектов для выведения на дисплей.
    TODO: Возможно, необходимо расширить функции объекта и 
    сделать его интерфейсным для работы с дисплеем вместо 
    самого дисплея. Это позволит снизить сложность кастомизации 
    визуального пространства для пользователя. 
    NOTE: нельзя создать DisplayWidget заранее, потому что это 
    повлечет необходимость создания qapplication при инициализации 
    библиотек."""

    def __init__(self):
        self.interactives = []
        self.display = None

    def add(self, obj, color=default_color()):
        from zencad.interactive.displayable import Displayable

        obj = evalcache.unlazy_if_need(obj)

        if isinstance(obj, Displayable):
            obj.bind_to_scene(self)
            iobj = obj
        else:
            iobj = create_interactive_object(obj, color)
            self.add(iobj)

        return iobj

    def add_interactive_object(self, iobj):
        self.interactives.append(iobj)

        if self.display is not None:
            self.display.display_interactive_object(iobj)
