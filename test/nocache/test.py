#!/usr/bin/env python3
#coding: utf-8

from zencad import *

lazy.diag = True
#lazy.diag_values = True
#lazy.print_invokes = True

m = box(50)

mt = translate(10,10,10) * translate(10,10,10)
#disp(m)
#translate(10,10,10).unlazy()
#(translate(10,10,10) * translate(10,10,10)).unlazy()
#evalcache.print_tree(translate(10,10,10) * translate(10,10,10))
#evalcache.lazy.lazydo(, debug=True)
disp(m.translate(10,10,10))
#print(translate(10,10,10))
#print(translate(10,10,10))
#evalcache.print_tree(translate(10,10,10)(m))
#evalcache.lazy.lazydo(mt, debug=True)
#evalcache.lazy.unlazy(mt, debug=True)
show()