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

    # diag=True,
    # diag_values=True,
    # print_invokes=True,
    # fastdo=True
)

diag = None
ensave = None
desave = None
onplace = None
status_notify = None


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
        disable_lazy()
        arrs = evalcache.lazy.tree_needeval(root)
        comm.send({"cmd": "evalcache", "subcmd": "progress",
                   "toload": len(arrs.toload), "toeval": len(arrs.toeval)})
        restore_lazy()

    def ftcb(root):
        pass

    def fncb(root, obj):
        disable_lazy()
        arrs = evalcache.lazy.tree_needeval(root)
        comm.send({"cmd": "evalcache", "subcmd": "progress",
                   "toload": len(arrs.toload), "toeval": len(arrs.toeval)})
        restore_lazy()

    lazy.set_start_tree_evaluation_callback(stcb)
    lazy.set_start_node_evaluation_callback(sncb)
    lazy.set_fini_tree_evaluation_callback(ftcb)
    lazy.set_fini_node_evaluation_callback(fncb)
