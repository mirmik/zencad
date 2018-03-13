#!/usr/bin/env python3

from setuptools import setup, Extension, Command

#class bdist_wheel(Command):
#    def finalize_options(self):
#        from sys import platform as _platform
#        platform_name = get_platform()
#        if _platform == "linux" or _platform == "linux2":
#            # Linux
#            platform_name = 'manylinux1_x86_64'
#
#        Command.finalize_options(self)
#        self.universal = True
#        self.plat_name_supplied = True
#        self.plat_name = platform_name

#zenlib = Extension('zenlib',
#    extra_compile_args = ["-std=c++14", '-DQT_NO_VERSION_TAGGING'],
#
#    define_macros = [('MAJOR_VERSION', '1'), ('MINOR_VERSION', '0')],
#
#    include_dirs = [
#    	'/usr/local/include', 
#    	'/usr/include/oce', 
#    	"src",
#    	"/home/mirmik/Qt/5.10.1/gcc_64/include/"
#    ],
#    
#    libraries = [
#    	'Qt5Core', 
#        'Qt5Widgets', 
#        'Qt5Test', 
#        'Qt5Gui', 
#        'Qt5OpenGL',
#
#        'TKernel',
#        'TKMath',
#        'TKG3d',
#        'TKBRep',
#        'TKGeomBase',
#        'TKGeomAlgo',
#        'TKTopAlgo',
#        'TKPrim',
#        'TKBO',
#        'TKBool',
#        'TKOffset',
#        'TKService',
#        'TKV3d',
#        'TKOpenGl',
#        'TKFillet',
#        'TKSTL'
#    ],
#    
#    library_dirs = ['/usr/local/lib'],
#    sources = [
#    	"src/zencad/base.cpp", 
#        "src/zencad/solid.cpp", 
#        "src/zencad/boolops.cpp", 
#        "src/zencad/cache.cpp", 
#        "src/zencad/pywrap.cpp", 
#        "src/zencad/trans.cpp", 
#        "src/zencad/topo.cpp",
#        "src/zencad/ZenWidget.cpp", 
#        "src/zencad/DisplayWidget.cpp", 
#        "src/zencad/ZenWidget.h.cxx", 
#        "src/zencad/DisplayWidget.h.cxx", 
#        "src/zencad/widget.cpp",
#   	]
#)

setup(
	name = 'zencad',
	packages = ['zencad'],
	version = '0.1.7',
	license='MIT',
	description = 'CAD system for righteous zen programmers ',
	author = 'Sorokin Nikolay',
	author_email = 'mirmikns@yandex.ru',
	url = 'https://github.com/mirmik/zencad',
	keywords = ['testing', 'cad'],
	classifiers = [],

   include_package_data=True,
    package_data={'zencad': ['zenlib.so']},
)
