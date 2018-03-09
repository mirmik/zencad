#!/usr/bin/env python3

from licant.cxx_modules import application, doit
from licant.modules import submodule

import licant
import licant.libs

licant.libs.include("gxx")

qt_include_path = "~/Qt/5.10.1/gcc_64/include/"

application("dzencad-display",
    target = "dzencad-display",

	sources = ["main.cpp", "DzenWidget.cpp", "DisplayWidget.cpp"],
	
    moc = ["DisplayWidget.h", "DzenWidget.h"],

	include_paths = [
		qt_include_path,
		#qt_include_path + "QtCore", 
		#qt_include_path + "QtWidgets", 
		#qt_include_path + "QtOpenGL", 
		#qt_include_path + "QtGui", 
	   '/usr/include/oce',
		"./",
	],
	
    cxx_flags = '-fPIC -L/home/mirmik/Qt/5.10.1/gcc_64/include/QtCore -DQT_NO_VERSION_TAGGING',
	
    libs = [
		'Qt5Core', 
        'Qt5Widgets', 
        #'Qt5Test', 
        'Qt5Gui', 
        'Qt5OpenGL',

    	'TKernel',
    	'TKMath',
    	#'TKG3d',
    	'TKBRep',
    	#'TKGeomBase',
    	#'TKGeomAlgo',
    	'TKTopAlgo',
    	'TKPrim',
    	#'TKBO',
    	#'TKBool',
    	#'TKOffset',
    	'TKService',
    	'TKV3d',
    	'TKOpenGl',
    	#'TKFillet',
    ],

    include_modules = [
        submodule("gxx.print", "cout"),
        submodule("gxx.dprint", "cout"),
        submodule("gxx", "posix"),
        submodule("gxx.include"),
    ], 
)
doit("dzencad-display")

licant.make.copy(src = "dzencad-display", tgt = "target")
licant.make.doit("target")
