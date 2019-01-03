import os
import zencad
import pyservoce
import evalcache
from zencad.lazifier import lazyfile
from zencad.lazifier import lazyhash
from zencad.lazifier import lazy

@lazyfile("path")
def to_stl(model, path, delta):
	pyservoce.make_stl(model, path, delta)

@lazyfile("path")
def to_brep(model, path):
	pyservoce.brep_write(model, path)

def from_brep(path):
	"""Загрузить объект из файла его brep представления

	Политика хеширования в данном случае требует учета возможности изменения
	файла. Поэтому в хэш загружаемого объекта подмешивается дата модификации
	файла. Объект не кешируется, потому как операция восстановления из кэша
	ничем не отличается от загрузки из файла.
	"""
	f = lazy(lambda p: pyservoce.brep_read(p), hint = str(os.path.getmtime(path)))
	obj = f(path)
	evalcache.nocache(obj)
	return obj


