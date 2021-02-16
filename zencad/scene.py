#!/usr/bin/env python3

import evalcache

from zencad.interactive_object import InteractiveObject
from zencad.interactive_object import ShapeInteractiveObject
from zencad.interactive_object import create_interactive_object

from zencad.axis import Axis
from zencad.shape import Shape, LazyObjectShape
from zencad.util import to_Vertex, to_GeomPoint

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
        self.objects = []
        self.interactives = []
        self.display = None

    def add(self, obj, color=None):
        if isinstance(obj, LazyObjectShape):
            obj = obj.unlazy()

        if isinstance(obj, evalcache.LazyObject):
            if isinstance(obj, Shape):
                if False:
                    print("Warning: Scene.add: wrong wrapped object")
            obj = obj.unlazy()

        if isinstance(obj, (Shape, Axis)):
            iobj = create_interactive_object(obj, color)
            self.add_interactive_object(iobj)

        elif isinstance(obj, InteractiveObject):
            iobj = obj
            self.add_interactive_object(iobj)

        elif isinstance(obj, numpy.ndarray):
            iobj = create_interactive_object(to_GeomPoint(obj))
            self.add_interactive_object(iobj)

        elif isinstance(obj, list):
            iobj = [self.add(item, color) for item in obj]

        else:
            raise Exception(
                f"Unresolved object type, __class__:{obj.__class__}")

        return iobj

    def add_interactive_object(self, iobj):
        self.interactives.append(iobj)

        if self.display is not None:
            self.display.display_interactive_object(iobj)
