import evalcache
import evalcache.dircache
from evalcache.lazyfile import LazyFile

import hashlib

lazy = evalcache.Lazy(cache = evalcache.DirCache(".evalcache"), algo = hashlib.sha256)
lazyfile = LazyFile()