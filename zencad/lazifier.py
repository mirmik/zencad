import evalcache
import evalcache.dircache
from evalcache.lazyfile import LazyFile

import hashlib
import os

cachepath = os.path.expanduser("~/.zencad-cache")

lazy = evalcache.Lazy(cache = evalcache.DirCache(cachepath), algo = hashlib.sha512)
lazyfile = LazyFile()

def disable_cache():
	lazy.encache = False
	lazy.decache = False

def test_mode():
	disable_cache()
	lazy.diag = True