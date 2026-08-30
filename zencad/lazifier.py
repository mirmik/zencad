import hashlib

import evalcache
import evalcache.dircache
import evalcache.dircache_v2
from evalcache.lazyfile import LazyFile

from zencad.cache_config import (
    CacheConfiguration,
    prepare_cache_directory,
    resolve_cache_configuration,
)


algo = hashlib.sha512


class DisabledCache:
    """Dict-like EvalCache backend that never reads or writes anything."""

    def __contains__(self, key):
        return False

    def __getitem__(self, key):
        raise KeyError(key)

    def __setitem__(self, key, value):
        return None

    def __delitem__(self, key):
        raise KeyError(key)

    def keys(self):
        return []

    def makePathTo(self, key):
        raise RuntimeError(
            "EvalCache file storage is unavailable while cache is disabled"
        )

    def clean_tmp(self):
        return None


def _cache_backend(configuration):
    if not configuration.enabled:
        return DisabledCache()
    directory = prepare_cache_directory(configuration.directory)
    return evalcache.dircache_v2.DirCache_v2(str(directory))


_cache_configuration = resolve_cache_configuration()
cachepath = str(_cache_configuration.directory)
lazy = evalcache.Lazy(
    cache=_cache_backend(_cache_configuration),
    algo=algo,
    encache=_cache_configuration.enabled,
    decache=_cache_configuration.enabled,
    onbool=True,
    onstr=True,
    pedantic=True,

    # diag=True,
    # diag_values=True,
    # print_invokes=True,
    # fastdo=True
)


def get_cache_configuration():
    return _cache_configuration


def apply_cache_configuration(configuration):
    global _cache_configuration, cachepath
    if not isinstance(configuration, CacheConfiguration):
        raise TypeError("configuration must be a CacheConfiguration")

    backend = _cache_backend(configuration)
    lazy.cache = backend
    lazy.encache = configuration.enabled
    lazy.decache = configuration.enabled
    _cache_configuration = configuration
    cachepath = str(configuration.directory)
    return configuration

diag = None
ensave = None
desave = None
onplace = None
status_notify = None


def _lazy_object_label(obj):
    generic = getattr(obj, "generic", None)
    value = getattr(generic, "__lazyvalue__", None)
    if value is None:
        value = getattr(obj, "__lazyvalue__", None)
    name = getattr(value, "__qualname__", None)
    if name is None:
        name = getattr(value, "__name__", None)
    if name is None and value is not None:
        name = type(value).__name__
    if name is None:
        name = type(obj).__name__
    return str(name)[:120]


def _lazy_object_operation(obj):
    if getattr(obj, "__lazyheap__", False):
        return "memory"
    if (
        getattr(obj, "__decache__", False)
        and obj.__lazyhexhash__ in obj.__lazybase__.cache
    ):
        return "load"
    return "evaluate"


def disable_lazy():
    global ensave, desave, onplace, diag, status_notify
    ensave = lazy.encache
    desave = lazy.decache
    diag = lazy.diag
    onplace = lazy.onplace
    status_notify = lazy.status_notify
    lazy.diag = False
    lazy.encache = False
    lazy.decache = False
    lazy.onplace = True
    lazy.status_notify = False


def restore_lazy():
    lazy.onplace = onplace
    lazy.encache = ensave
    lazy.decache = desave
    lazy.diag = diag
    lazy.status_notify = status_notify


def install_evalcahe_notication(comm):
    #    if zencad.configure.CONFIGURE_WITHOUT_EVALCACHE_NOTIFIES:
    #        return

    lazy.status_notify_enable(True)

    def stcb(root):
        arr = evalcache.lazy.tree_objects(root)
        comm.send({"cmd": "evalcache", "subcmd": "newtree",
                   "len": len(arr), "root": root.__lazyhexhash__})

    def sncb(root, obj):
        operation = _lazy_object_operation(obj)
        object_name = _lazy_object_label(obj)
        disable_lazy()
        try:
            arrs = evalcache.lazy.tree_needeval(root)
        finally:
            restore_lazy()
        comm.send({"cmd": "evalcache", "subcmd": "progress",
                   "toload": len(arrs.toload), "toeval": len(arrs.toeval),
                   "operation": operation, "object": object_name})

    def ftcb(root):
        pass

    def fncb(root, obj):
        disable_lazy()
        try:
            arrs = evalcache.lazy.tree_needeval(root)
        finally:
            restore_lazy()
        comm.send({"cmd": "evalcache", "subcmd": "progress",
                   "toload": len(arrs.toload), "toeval": len(arrs.toeval)})

    lazy.set_start_tree_evaluation_callback(stcb)
    lazy.set_start_node_evaluation_callback(sncb)
    lazy.set_fini_tree_evaluation_callback(ftcb)
    lazy.set_fini_node_evaluation_callback(fncb)
