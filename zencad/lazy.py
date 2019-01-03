import evalcache
import evalcache.dircache
from evalcache.lazyfile import LazyFile

import hashlib
import os

lazy = evalcache.Lazy(cache = evalcache.DirCache(os.path.expanduser("~/.zencad-cache")), algo = hashlib.sha512)
lazyfile = LazyFile()

def disable_cache():
	lazy.encache = False
	lazy.decache = False

def test_mode():
	disable_cache()
	lazy.diag = True