import evalcache
import evalcache.dircache
from evalcache.lazyfile import LazyFile

import hashlib

lazy = evalcache.Lazy(cache = evalcache.DirCache(".evalcache"), algo = hashlib.sha256)
lazyfile = LazyFile()

def disable_cache():
	lazy.encache = False
	lazy.decache = False

def test_mode():
	disable_cache()
	lazy.diag = True