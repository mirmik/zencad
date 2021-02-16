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
import pyservoce
import evalcache
from zencad.lazifier import lazy


@lazy.file_creator(pathfield="path")
def to_stl(model, path, delta):
    path = os.path.expanduser(path)
    pyservoce.make_stl(model, path, delta)


@lazy.file_creator(pathfield="path")
def to_brep(model, path):
    path = os.path.expanduser(path)
    pyservoce.brep_write(model, path)


def from_brep(path):
    """Загрузить объект из файла его brep представления."""
    path = os.path.expanduser(path)
    f = lazy(lambda p: pyservoce.brep_read(p),
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


#from zencad.convert.svg import shape_to_svg_string
#from zencad.convert.svg import shape_to_svg
#from zencad.convert.svg import svg_to_shape
