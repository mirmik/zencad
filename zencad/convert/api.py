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

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
from OCP.TopoDS import TopoDS_Shape
from zencad.occ_compat import read_brep, write_brep


def _to_stl(shp, path, delta):
    path = os.path.expanduser(path)

    mesh = BRepMesh_IncrementalMesh(shp.Shape(), delta)

    if mesh.IsDone() is False:
        return False

    stl_writer = StlAPI_Writer()
    return stl_writer.Write(shp.Shape(), path)


@lazy.file_creator(pathfield="path")
def _cached_to_stl(model, path, delta):
    return _to_stl(model, path, delta)


def to_stl(model, path, delta):
    if not zencad.lazifier.get_cache_configuration().enabled:
        return _to_stl(evalcache.unlazy_if_need(model), path, delta)
    return _cached_to_stl(model, path, delta)


def _to_brep(model, path):
    if not write_brep(model.Shape(), path):
        raise OSError(f"Failed to write BREP file: {path}")


@lazy.file_creator(pathfield="path")
def _cached_to_brep(model, path):
    return _to_brep(model, path)


def to_brep(model, path):
    if not zencad.lazifier.get_cache_configuration().enabled:
        return _to_brep(evalcache.unlazy_if_need(model), path)
    return _cached_to_brep(model, path)


def _from_brep(path):
    from zencad.geom.shape import Shape
    path = os.path.expanduser(path)

    shp = TopoDS_Shape()
    if not read_brep(shp, path):
        raise OSError(f"Failed to read BREP file: {path}")
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


def _to_svg(model, path, color=(0, 0, 0), mapping=False):
    path = os.path.expanduser(path)
    string = zencad.convert.svg.shape_to_svg_string(model, color, mapping)
    with open(path, "wb") as f:
        f.write(string.encode("utf-8"))


_cached_to_svg = lazy.file_creator(
    pathfield="path",
    prevent_unwrap_in_child=["model"],
)(_to_svg)


def to_svg(model, path, color=(0, 0, 0), mapping=False):
    if not zencad.lazifier.get_cache_configuration().enabled:
        return _to_svg(
            evalcache.unlazy_if_need(model),
            path,
            color,
            mapping,
        )
    return _cached_to_svg(model, path, color, mapping)


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
