import evalcache
import evalcache.dircache
import evalcache.dircache_v2
from evalcache.lazyfile import LazyFile

import hashlib
import os

cachepath = os.path.expanduser("~/.zencad-cache")
algo = hashlib.sha512

lazy = evalcache.Lazy(cache = evalcache.dircache_v2.DirCache_v2(cachepath), algo = algo)

def disable_cache():
	lazy.encache = False
	lazy.decache = False

def test_mode():
	disable_cache()
	lazy.diag = True