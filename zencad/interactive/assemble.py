import evalcache
import numpy

from zencad.settings import Settings
from zencad.geom.transformable import Transformable
from zencad.geom.trans import rotate, translate
from zencad.geom.exttrans import nulltrans
from zencad.interactive.line import arrow

from zencad.geom.trans import rotateZ, rotateY, rotate, translate
from zencad.util import vector3, point3
from zencad.color import Color as color

from zencad.interactive import create_interactive_object
from zencad.interactive.displayable import Displayable


class unit(Transformable, Displayable):
    """Базовый класс для использования в кинематических цепях и сборках

    Вычисляет свою текущую позицию исходя из дерева построения.
    Держит список наследников, позиция которых считается относительно него.    
    """

    def __init__(self,
                 parts=[],
                 parent=None,
                 shape=None,
                 name=None,
                 location=nulltrans()):
        self.parent = parent
        self.location = evalcache.unlazy_if_need(location)
        self.global_location = self.location
        self.name = name
        self.color = None
        self.dispobjects = []
        self.scene = None

        self.shapes_holder = []

        self.views = set()
        self.childs = set()

        if parent is not None:
            parent.add_child(self)

        for obj in parts:
            self.add(obj)

    def add_child(self, child):
        child.parent = self
        self.childs.add(child)

    def link(self, child):
        self.add_child(child)

    def location_update(self, deep=True, view=True):
        if self.parent is None:
            self.global_location = self.location

        else:
            self.global_location = self.parent.global_location * self.location

        if deep:
            for c in self.childs:
                c.location_update(deep=True, view=view)

        if view:
            self._apply_view_location(False)

    def relocate(self, location, deep=False, view=True):
        self.location = evalcache.unlazy_if_need(location)
        self.location_update(deep=deep, view=False)

        if view:
            self._apply_view_location(deep=deep)

    def set_objects(self, objects):
        self.dispobjects = objects

    def add_object(self, d):
        self.dispobjects.append(d)

        if self.scene:
            self.scene.add(d)
            self.views.add(d)

    def add(self, obj, color=None):
        uo = evalcache.unlazy_if_need(obj)
        interobj = create_interactive_object(uo, color=color)
        self.add_object(interobj)
        return interobj

    def add_shape(self, obj, color):
        print("'add_shape' is deprecated. use 'add' method instead.")
        self.add(obj, color)

    def add_triedron(self, length=10, width=1, arrlen=1,
                     xcolor=color.red, ycolor=color.green, zcolor=color.blue):
        self.xaxis = arrow(point3(0, 0, 0), vector3(
            length, 0, 0), color=xcolor, arrlen=arrlen, width=width)
        self.yaxis = arrow(point3(0, 0, 0), vector3(
            0, length, 0), color=ycolor, arrlen=arrlen, width=width)
        self.zaxis = arrow(point3(0, 0, 0), vector3(
            0, 0, length), color=zcolor, arrlen=arrlen, width=width)

        self.dispobjects.append(self.xaxis)
        self.dispobjects.append(self.yaxis)
        self.dispobjects.append(self.zaxis)

    def set_color(self, *args, **kwargs):
        self.color = color(*args, **kwargs)

        for o in self.dispobjects:
            o.set_color(self.color)

    def print_tree(self, tr=0):
        s = "\t" * tr + str(self)
        print(s)

        for c in self.childs:
            c.print_tree(tr+1)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return repr(self)

    def _apply_view_location(self, deep):
        """Перерисовать положения объектов юнита во всех зарегестрированных 
        view. Если deep, применить рекурсивно."""

        for v in self.views:
            v.relocate(self.global_location)

        if deep:
            for c in self.childs:
                c._apply_view_location(deep)

    def bind_to_scene(self, scene):
        self.location_update(deep=True)

        for d in self.dispobjects:
            scene.add_interactive_object(d)
            self.views.add(d)

        self._apply_view_location(deep=False)

        for c in self.childs:
            c.bind_to_scene(scene)

        self.scene = scene

    def transform(self, trsf):
        self.relocate(trsf * self.location, deep=True, view=True)
        return self

    def copy(self, deep=True):
        parts = [obj.copy(bind_to_scene=False) for obj in self.dispobjects]

        if deep:
            parts = parts + [child.copy(deep=True) for child in self.childs]

        cpy = zencad.assemble.unit(
            parent=self.parent,
            location=self.location,
            parts=parts,
            name=self.name
        )

        cpy.location_update()

        if self.scene:
            cpy.bind_scene(self.scene)

        return cpy

    def union_shape(self):
        acc = zencad.nullshape()
        for p in self.dispobjects:
            if isinstance(p, interactive_object) and p.is_shape():
                s = p.object
                acc += s
        return acc


class kinematic_unit(unit):
    """Кинематическое звено задаётся двумя системами координат,
    входной и выходной. Изменение кинематических параметров изменяет
    положение выходной СК относительно входной"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output = unit(parent=self)

    def senses(self):
        """Возвращает кортеж тензоров производной по положению
        по набору кинематических координат
        в собственной системе координат в формате (w, v)"""

        raise NotImplementedError

    def set_coords(self, coords, **kwargs):
        """Устанавливает модельное положение звена согласно 
        переданным координатам"""

        raise NotImplementedError

    def link(self, arg):
        """Присоединить объект arg к выходной СК.

        Для kinematic_unit метод link переопределяется,
        с тем, чтобы линковка происходила не ко входной, 
        а к выходной СК"""

        self.output.link(arg)


class kinematic_unit_one_axis(kinematic_unit):
    """Кинематическое звено специального вида,
    взаимное положение СК которого может быть описано одним 3вектором

    ax - вектор, задающий ось и направление. задаётся с точностью до длины.
    mul - линейный коэффициент масштабирования входной координаты.
    """

    def __init__(self, axis, mul=1, **kwargs):
        super().__init__(**kwargs)
        self.coord = 0
        self.axis = vector3(axis)
        self.axis = self.axis.normalize()
        self.mul = mul
        self.axmul = self.axis * self.mul

    # override
    def senses(self):
        return (self.sensivity(),)

    # override
    def set_coords(self, coords, **kwargs):
        self.set_coord(coords[0], **kwargs)

    def update_coord(self, coord):
        self.coord = coord

    def sensivity(self):
        raise NotImplementedError

    def set_coord(self, coord, **kwargs):
        raise NotImplementedError


class rotator(kinematic_unit_one_axis):
    def sensivity(self):
        """Возвращает тензор производной по положению
        в собственной системе координат в формате (w, v)"""
        return (self.axmul, vector3())

    def set_coord(self, coord, **kwargs):
        self.coord = coord
        self.output.relocate(rotate(self.axis, coord * self.mul), **kwargs)


class actuator(kinematic_unit_one_axis):
    def sensivity(self):
        """Возвращает тензор производной по положению
        в собственной системе координат в формате (w, v)"""
        return (vector3(), self.axmul)

    def set_coord(self, coord, **kwargs):
        self.coord = coord
        self.output.relocate(translate(
            self.axis * coord * self.mul), **kwargs)


class planemover(kinematic_unit):
    """Кинематическое звено с двумя степенями свободы для перемещения
    по плоскости"""

    def __init__(self):
        super().__init__(**kwargs)
        self.x = 0
        self.y = 0

    def senses(self):
        return (
            (vector3(1, 0, 0), vector3()),
            (vector3(0, 1, 0), vector3())
        )

    def set_coords(self, coords, **kwargs):
        self.x = coord[0]
        self.y = coord[1]
        self.output.relocate(
            translate(vector3(self.x, self.y, 0)), **kwargs)


class spherical_rotator(kinematic_unit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._yaw = 0
        self._pitch = 0

    def senses(self):
        raise NotImplementedError
        # return (
        #	(vector3(1,0,0), vector3()),
        #	(vector3(0,1,0), vector3())
        # )

    def set_yaw(self, angle, **kwargs):
        self._yaw = angle
        self.update_position(**kwargs)

    def set_pitch(self, angle, **kwargs):
        self._pitch = angle
        self.update_position(**kwargs)

    def set_coords(self, coords, **kwargs):
        self._yaw = coord[0]
        self._pitch = coord[1]
        self.update_position(**kwargs)

    def update_position(self, **kwargs):
        self.output.relocate(rotateZ(self._yaw)
                             * rotateY(self._pitch))


def for_each_unit(u, foo):
    foo(u)
    for c in u.childs:
        for_each_unit(c, foo)
