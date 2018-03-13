#!/usr/bin/env python3

from licant.cxx_modules import application, shared_library, doit
from licant.modules import submodule, module

import licant
import licant.libs

qt_include_path = "~/Qt/5.10.1/gcc_64/include/"
qt_lib_path = "/home/mirmik/Qt/5.10.1/gcc_64/lib/"
boost_lib_path = "./third-party/"
python_include_path = "/usr/include/python3.5/"

licant.libs.include("gxx")

module('libraries', 
    include_paths = [
       '/usr/include/oce',
       './src',
        "./",
        qt_include_path,
        python_include_path,
    ],
    
    cxx_flags = '-fPIC -DQT_NO_VERSION_TAGGING',
    cc_flags = '-fPIC',

    libs = [
        'Qt5Core', 
        'Qt5Widgets', 
        'Qt5Test', 
        'Qt5Gui', 
        'Qt5OpenGL',

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

    include_modules = [
        submodule("gxx.print", "cout"),
        submodule("gxx.dprint", "cout"),
        submodule("gxx", "posix"),
        submodule("gxx.include"),
    ], 
)

shared_library("zenlib",
    target = "zencad/zenlib.so",
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
    include_modules = [submodule("libraries")],
)
doit("zenlib")
