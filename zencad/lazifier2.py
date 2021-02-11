import os
import hashlib

import evalcache
import evalcache.dircache
import evalcache.dircache_v2
from evalcache.lazyfile import LazyFile

cachepath = os.path.expanduser("~/.zencadcache")
algo = hashlib.sha512

lazy = evalcache.Lazy(
    cache=evalcache.dircache_v2.DirCache_v2(cachepath), 
    algo=algo, 
    onbool=True,
    onstr=True,
    pedantic=True,
    diag=True,
    diag_values=True,
    #print_invokes=True

    #fastdo = True
)
