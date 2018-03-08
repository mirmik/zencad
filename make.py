#!/usr/bin/env python3

from licant.cxx_modules import application, doit

application("target",
	sources = ["main.cpp", "occQt.cpp", "occView.cpp", "res.cpp"],
	moc = ["occQt.h", "occView.h"],

	include_paths = [
		"~/Qt/5.10.1/gcc_64/include",
		"~/Qt/5.10.1/gcc_64/include/QtCore", 
		"~/Qt/5.10.1/gcc_64/include/QtWidgets", 
		"~/Qt/5.10.1/gcc_64/include/QtOpenGL", 
		"~/Qt/5.10.1/gcc_64/include/QtGui", 
		'/usr/include/oce',
		"./",
	],
	cxx_flags = '-fPIC -L/home/mirmik/Qt/5.10.1/gcc_64/include/QtCore -DQT_NO_VERSION_TAGGING',
	libs = [
		'Qt5Core', 'Qt5Widgets', 'Qt5Test', 'Qt5Gui', 'Qt5OpenGL',

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
    ]
)

doit("target")