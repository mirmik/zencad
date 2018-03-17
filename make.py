#!/usr/bin/env python3

from licant.cxx_modules import shared_library
from licant.modules import module

import licant
import licant.libs

licant.libs.include("gxx")

libqt_include_path = "/usr/include/x86_64-linux-gnu/qt5/"
liboce_include_path = "/usr/include/oce"
python_include_prefix = "/usr/include/"

module('liboce', 
	libs = [     
		'TKernel',
        'TKMath',
        'TKG3d',
        'TKBRep',
        'TKGeomBase',
        'TKGeomAlgo',
        'TKTopAlgo',
        'TKPrim',
        'TKBO',
        'TKBool',
        'TKOffset',
        'TKService',
        'TKV3d',
        'TKOpenGl',
        'TKFillet',
        'TKSTL',
        'TKBin',
    ],
    include_paths = [liboce_include_path]    
)

module('libqt', 
	libs = [    
        'Qt5Core', 
        'Qt5Widgets', 
        'Qt5Test', 
        'Qt5Gui', 
        'Qt5OpenGL',
    ],
    include_paths = [libqt_include_path]    
)

def registry_library(py):
	shared_library("zenlib." + py,
	    target = "zencad/" + py + "/zenlib.so",
	    builddir = "build/" + py,
	    
	    cxx_flags = '-fPIC -DQT_NO_VERSION_TAGGING',
	    cc_flags = '-fPIC',
	
	    srcdir = "src",
	    sources = [
	        "zencad/base.cpp", 
	        "zencad/solid.cpp", 
	        "zencad/wire.cpp", 
	        "zencad/boolops.cpp", 
	        "zencad/cache.cpp", 
	        "zencad/pywrap.cpp", 
	        "zencad/trans.cpp", 
	        "zencad/topo.cpp",
	        "zencad/ZenWidget.cpp", 
	        "zencad/DisplayWidget.cpp", 
	        "zencad/widget.cpp",
	    ],
	    moc = ["zencad/DisplayWidget.h", "zencad/ZenWidget.h"],    
	    include_modules = [
            "libqt", 
            "liboce",
	    	("gxx", "posix"),
            ("gxx.print", "cout"),
            ("gxx.dprint", "cout")
        ],
	    include_paths = [
            ".", 
            "src", 
            python_include_prefix + py
        ]
	)

registry_library("python2.7")
registry_library("python3.5")
registry_library("python3.5m")

@licant.routine
def local35():
    licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python3.5/zenlib.so")
    licant.do("zencad/zenlib.so", "makefile")

@licant.routine
def local35m():
    licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python3.5m/zenlib.so")
    licant.do("zencad/zenlib.so", "makefile")

@licant.routine
def local27():
    licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python2.7/zenlib.so")
    licant.do("zencad/zenlib.so", "makefile")

licant.add_makefile_target(tgt = "all", targets = [
    "zenlib.python2.7",
    "zenlib.python3.5",
    "zenlib.python3.5m",
])

licant.ex(default = "all")