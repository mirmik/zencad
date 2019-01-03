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
	def impl(path):
		return pyservoce.brep_read(path)
	f = lazy(impl, hint = str(os.path.getmtime(path)))
	obj = f(path)
	evalcache.nocache(obj)
	return obj


