import evalcache
import numpy

from zencad.settings import Settings
from zencad.geom.transformable import Transformable
from zencad.geom.exttrans import nulltrans


class ShapeView:
    def __init__(self, sctrl):
        self.sctrl = sctrl

    def relocate(self, trans):
        self.sctrl.relocate(trans)

    def hide(self, en):
        self.sctrl.hide(en)

    def transform(self, trsf):
        self.sctrl.transform(trsf)


class unit(Transformable):
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

        if shape is not None:
            print(
                "zencad.assemble.unit: `shape` option is deprecated. use `parts` option instead")
            self.shape = shape
            self.add_shape(self.shape)

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

    def set_shape(self, shp):
        raise Exception(
            "zencad.assemble.unit: set_shape function removed. Use `add_shape` instead.")

    def add_object(self, d):
        self.dispobjects.append(d)

    def add(self, obj, color=None):
        uo = obj.unlazy()

        if isinstance(obj, zencad.assemble.unit):
            return self.add_child(obj)
        elif isinstance(uo, pyservoce.Shape):
            return self.add_shape(obj, color)
        elif isinstance(uo, pyservoce.interactive_object):
            return self.add_object(obj)
        else:
            raise Exception("unresolved unit part type", obj, uo)

    def add_shape(self, shp, color=None):
        controller = zencad.interactive_object(shp)

        if color is not None:
            controller.set_color(pyservoce.color(color))
        else:
            controller.set_color(pyservoce.color(zencad.default_color))

        self.dispobjects.append(controller)
        self.shapes_holder.append(shp)
        return controller

    def add_triedron(self, length=10, width=1, arrlen=1,
                     xcolor=pyservoce.red, ycolor=pyservoce.green, zcolor=pyservoce.blue):
        self.xaxis = pyservoce.draw_arrow(pyservoce.point3(0, 0, 0), pyservoce.vector3(
            length, 0, 0), clr=xcolor, arrlen=arrlen, width=width)
        self.yaxis = pyservoce.draw_arrow(pyservoce.point3(0, 0, 0), pyservoce.vector3(
            0, length, 0), clr=ycolor, arrlen=arrlen, width=width)
        self.zaxis = pyservoce.draw_arrow(pyservoce.point3(0, 0, 0), pyservoce.vector3(
            0, 0, length), clr=zcolor, arrlen=arrlen, width=width)

        self.dispobjects.append(self.xaxis)
        self.dispobjects.append(self.yaxis)
        self.dispobjects.append(self.zaxis)

    def set_color(self, *args, **kwargs):
        self.color = pyservoce.color(*args, **kwargs)

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

    def bind_scene(self,
                   scene,
                   color=None,
                   deep=True):
        self.location_update(deep)

        for d in self.dispobjects:
            if color is not None:
                d.set_color(zencad.util.color(color))
            scene.viewer.display(d)
            self.views.add(ShapeView(d))

        self._apply_view_location(deep=False)

        if deep:
            for c in self.childs:
                c.bind_scene(scene, color=color, deep=True)

        self.scene = scene
        return self

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
            if isinstance(p, pyservoce.interactive_object) and p.is_shape():
                s = p.object
                acc += s
        return acc


class kinematic_unit(unit):
    """Кинематическое звено задаётся двумя системами координат,
    входной и выходной. Изменение кинематических параметров изменяет
    положение выходной СК относительно входной"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output = zencad.assemble.unit(parent=self)

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
        self.axis = pyservoce.vector3(axis)
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
        return (self.axmul, pyservoce.vector3())

    def set_coord(self, coord, **kwargs):
        self.coord = coord
        self.output.relocate(pyservoce.rotate(
            a=coord*self.mul, v=self.axis), **kwargs)


class actuator(kinematic_unit_one_axis):
    def sensivity(self):
        """Возвращает тензор производной по положению
        в собственной системе координат в формате (w, v)"""
        return (pyservoce.vector3(), self.axmul)

    def set_coord(self, coord, **kwargs):
        self.coord = coord
        self.output.relocate(pyservoce.translate(
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
            (pyservoce.vector3(1, 0, 0), pyservoce.vector3()),
            (pyservoce.vector3(0, 1, 0), pyservoce.vector3())
        )

    def set_coords(self, coords, **kwargs):
        self.x = coord[0]
        self.y = coord[1]
        self.output.relocate(
            pyservoce.translate(pyservoce.vector3(self.x, self.y, 0)), **kwargs)


class spherical_rotator(kinematic_unit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._yaw = 0
        self._pitch = 0

    def senses(self):
        raise NotImplementedError
        # return (
        #	(pyservoce.vector3(1,0,0), pyservoce.vector3()),
        #	(pyservoce.vector3(0,1,0), pyservoce.vector3())
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
        self.output.relocate(pyservoce.rotateZ(self._yaw)
                             * pyservoce.rotateY(self._pitch))


def for_each_unit(u, foo):
    foo(u)
    for c in u.childs:
        for_each_unit(c, foo)
