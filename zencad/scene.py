#!/usr/bin/env python3

from zencad.interactive import *

from zencad.color import default_color
from zencad.interactive import create_interactive_object
from zencad.bbox import BoundaryBox


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

    def add(self, obj, color=None, display_mode=None, *, name=None):
        from zencad.interactive.displayable import Displayable

        if color is None:
            color = default_color()
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Scene object name must be a non-empty string")
            if any(getattr(item, "name", None) == name for item in self.interactives):
                raise ValueError(f"Duplicate scene object name: {name!r}")

        if isinstance(obj, Displayable):
            if display_mode is not None:
                setter = getattr(obj, "set_mesh_display_mode", None)
                if setter is None:
                    raise ValueError(
                        "display_mode is only supported for mesh objects"
                    )
                setter(display_mode)
            iobj = obj
            if name is not None:
                iobj.name = name
            obj.bind_to_scene(self)
        else:
            iobj = create_interactive_object(
                obj,
                color,
                display_mode=display_mode,
            )
            return self.add(iobj, name=name)

        return iobj

    def add_interactive_object(self, iobj):
        self.interactives.append(iobj)

        if self.display is not None:
            self.display.display_interactive_object(iobj)

    def boundbox(self):
        box = BoundaryBox()
        for inter in self.interactives:
            bbox = inter.boundbox()
            box.add(bbox)
        return box
