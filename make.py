#!/usr/bin/env python3

from licant.cxx_modules import application, shared_library, doit
from licant.modules import submodule, module

import licant
import licant.libs

qt_include_path = "~/Qt/5.10.1/gcc_64/include/"
qt_lib_path = "/home/mirmik/Qt/5.10.1/gcc_64/lib/"
boost_lib_path = "./third-party/"
python_include_path = "/usr/include/python3.5m/"

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

        'boost_python-py35',
        'boost_system',
    ],

    #objects = [
    #	"/usr/lib/x86_64-linux-gnu/libboost_python-py35.a",
    #	 qt_lib_path + "libQt5Core.la",
    #],

    include_modules = [
        submodule("gxx.print", "cout"),
        submodule("gxx.dprint", "cout"),
        submodule("gxx", "posix"),
        submodule("gxx.include"),
    ], 
)

shared_library("dzenlib",
    target = "dzencad/dzenlib.so",
    srcdir = "src",
    sources = [
        "dzencad/base.cpp", 
        "dzencad/solid.cpp", 
        "dzencad/boolops.cpp", 
        "dzencad/cache.cpp", 
        "dzencad/pywrap.cpp", 
        "dzencad/trans.cpp", 
        "dzencad/topo.cpp",
        "dzencad/DzenWidget.cpp", 
        "dzencad/DisplayWidget.cpp", 
        "dzencad/widget.cpp",
    ],
    moc = ["dzencad/DisplayWidget.h", "dzencad/DzenWidget.h"],    
    include_modules = [submodule("libraries")],
)
doit("dzenlib")
