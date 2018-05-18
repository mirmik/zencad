#!/usr/bin/env python3

from licant.cxx_modules import shared_library
from licant.modules import module, submodule
import licant
import licant.libs

python_include_prefix = "/usr/include/"

licant.libs.include("servoce")

def registry_library(py):
	shared_library("zenlib." + py,
		target = "zencad/" + py + "/zenlib.so",
		builddir = "build/" + py,
		
		cxx_flags = '-fPIC -DQT_NO_VERSION_TAGGING',
		cc_flags = '-fPIC',
		ld_flags = '-Wl,-rpath,\'$ORIGIN/\'',
	
		srcdir = "src",
		sources = [
			"pywrap.cpp",  
		],
		include_paths = [
			python_include_prefix + py
		],

		include_modules = [
			(("servoce_sources"))
		],

		#libs = ["servoce"]
	)

#licant.make.source("/usr/lib/libservoce.so")
#licant.make.copy(tgt = "zencad/libservoce.so", src = "/usr/lib/libservoce.so")

registry_library("python2.7")
registry_library("python3.5")
registry_library("python3.6")

def do_wheel(suffix):
	os.system("python{} setup.py bdist_wheel".format(suffix))

def install_egg(suffix):
	os.system("sudo python{} setup.py install".format(suffix))	

@licant.routine
def local35():
	os.system("rm zencad/libservoce.so")
	os.system("rm zencad/zenlib.so")
	licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python3.5/zenlib.so")
#	licant.do("zencad/libservoce.so")
	licant.do("zencad/zenlib.so", "makefile")

@licant.routine
def install35():
#	os.system("rm zencad/libservoce.so")
	os.system("rm zencad/zenlib.so")
	os.system("rm zencad/python3.5/zenlib.so")
	licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python3.5/zenlib.so")
#	licant.do("zencad/libservoce.so")
	licant.do("zencad/zenlib.so", "makefile")
	install_egg("3.5")

@licant.routine
def local36():
#	os.system("rm zencad/libservoce.so")
	os.system("rm zencad/zenlib.so")
	licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python3.6/zenlib.so")
	licant.do("zencad/zenlib.so", "makefile")

@licant.routine
def install36():
#	os.system("rm zencad/libservoce.so")
	os.system("rm zencad/zenlib.so")
	licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python3.5/zenlib.so")
	licant.do("zencad/zenlib.so", "makefile")
	install_egg("3.6")

@licant.routine
def local27():
#	os.system("rm zencad/libservoce.so")
	os.system("rm zencad/zenlib.so")
	licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python2.7/zenlib.so")
	licant.do("zencad/zenlib.so", "makefile")

@licant.routine
def install27():
#	os.system("rm zencad/libservoce.so")
	os.system("rm zencad/zenlib.so")
	licant.make.copy(tgt = "zencad/zenlib.so", src = "zencad/python3.5/zenlib.so")
	licant.do("zencad/zenlib.so", "makefile")
	install_egg("2.7")

licant.add_makefile_target(tgt = "all", targets = [
#	"zencad/libservoce.so",
	"zenlib.python2.7",
	"zenlib.python3.5",
	"zenlib.python3.6",
])

import os
@licant.routine
def wheels():
	licant.do("all", "makefile")

	def do_for_suffix(suffx):
		os.system("cp zencad/python{}/zenlib.so zencad/zenlib.so".format(suffx))
		os.system("python{} setup.py bdist_wheel".format(suffx))

	#os.system("mkdir -p dist")
	do_for_suffix("2.7")
	do_for_suffix("3.5")
	do_for_suffix("3.6")

@licant.routine
def publish():
	os.system("rm -rf dist")
	licant.do("wheels")
	os.system("twine upload dist/* --repository-url https://upload.pypi.org/legacy/")

@licant.routine
def distclean():
	os.system("rm -rf dist")
	os.system("rm -rf build")
	os.system("rm -rf zencad/python*")
	os.system("rm -rf zencad/__pycache__")
	os.system("rm -rf zencad/zenlib.so")
#	os.system("rm -rf zencad/libservoce.so")
	os.system("rm -rf zencad.egg-info")
	print("distclean success")

licant.ex(default = "all")