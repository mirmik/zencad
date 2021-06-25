"""
В этом файле определены операции экспорта и импорта геометрии.

Операции экспорта реализованы с применением evalcache.lazyfile,
что позволяет избежать множественных загрухок крайней ноды.

Политика хеширования в случае импорта требует учета возможности изменения
файла. Поэтому в хэш загружаемого объекта подмешивается дата его модификации.
Объект не кешируется, потому как операция восстановления из кэша
ничем не отличается от загрузки из файла.
"""

import zencad.convert.svg
import os
import zencad
import evalcache
from zencad.lazifier import lazy

from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepTools import breptools


def _to_stl(shp, path, delta):
    path = os.path.expanduser(path)

    mesh = BRepMesh_IncrementalMesh(shp.Shape(), delta)

    if mesh.IsDone() is False:
        return False

    stl_writer = StlAPI_Writer()
    stl_writer.Write(shp.Shape(), path)
    return True


@lazy.file_creator(pathfield="path")
def to_stl(model, path, delta):
    return _to_stl(model, path, delta)


def _to_brep(model, path):
    breptools.Write(model.Shape(), path)


@lazy.file_creator(pathfield="path")
def to_brep(model, path):
    return _to_brep(model, path)


def _from_brep(path):
    from zencad.geom.shape import Shape
    path = os.path.expanduser(path)

    shp = TopoDS_Shape()
    builder = BRep_Builder()

    breptools.Read(shp, path, builder)
    return Shape(shp)


def from_brep(path):
    """Загрузить объект из файла его brep представления.
    Если таймштамп загружаемого файла изменится, благодаря hint изменится его lazyhash"""
    path = os.path.expanduser(path)
    f = lazy(lambda p: _from_brep(p),
             hint=str(os.path.getmtime(path)))
    obj = f(path)
    evalcache.nocache(obj)
    return obj


@lazy.file_creator(pathfield="path", prevent_unwrap_in_child=["model"])
def to_svg(model, path, color=(0, 0, 0), mapping=False):
    path = os.path.expanduser(path)
    string = zencad.convert.svg.shape_to_svg_string(model, color, mapping)
    with open(path, "wb") as f:
        f.write(string.encode("utf-8"))


@lazy.lazy(prevent_unwrap_in_child=["model"])
def to_svg_string(model, color=(0, 0, 0), mapping=False):
    return zencad.convert.svg.shape_to_svg_string(model, color, mapping)


def from_svg(path):
    """Загрузить объект из файла его brep представления."""
    path = os.path.expanduser(path)

    f = lazy(lambda p: zencad.convert.svg.svg_to_shape(
        path), hint=str(os.path.getmtime(path)))
    obj = f(path)
    evalcache.nocache(obj)
    return obj


@lazy
def from_svg_string(string):
    reader = zencad.convert.svg.SvgReader()
    return reader.read_string(string)
