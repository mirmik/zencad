"""
В этом файле определены операции экспорта и импорта геометрии. 

Операции экспорта реализованы с применением evalcache.lazyfile,
что позволяет избежать множественных загрухок крайней ноды.

Политика хеширования в случае импорта требует учета возможности изменения
файла. Поэтому в хэш загружаемого объекта подмешивается дата его модификации. 
Объект не кешируется, потому как операция восстановления из кэша
ничем не отличается от загрузки из файла.
"""

import os
import zencad
import pyservoce
import evalcache
from zencad.lazifier import lazy


@lazy.file_creator(pathfield="path")
def to_stl(model, path, delta):
    pyservoce.make_stl(model, path, delta)


@lazy.file_creator(pathfield="path")
def to_brep(model, path):
    pyservoce.brep_write(model, path)


def from_brep(path):
    """Загрузить объект из файла его brep представления."""
    f = lazy(lambda p: pyservoce.brep_read(p), hint=str(os.path.getmtime(path)))
    obj = f(path)
    evalcache.nocache(obj)
    return obj
