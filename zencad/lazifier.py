import evalcache
import evalcache.dircache
from evalcache.lazyfile import LazyFile

import hashlib
import os

cachepath = os.path.expanduser("~/.zencad-cache")
algo = hashlib.sha512

lazy = evalcache.Lazy(cache = evalcache.DirCache(cachepath), algo = algo)
lazyhash_fast = evalcache.LazyHash(algo = algo, fastdo = True)
lazyhash = evalcache.LazyHash(algo = algo, fastdo = False)
lazyfile = LazyFile()

def disable_cache():
	lazy.encache = False
	lazy.decache = False

def test_mode():
	disable_cache()
	lazy.diag = True