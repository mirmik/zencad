import evalcache
import evalcache.dircache

import hashlib

lazy = evalcache.Lazy(cache = evalcache.DirCache(".evalcache"), algo = hashlib.sha256)