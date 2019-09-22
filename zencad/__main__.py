#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import zencad
import zencad.shower
import zencad.showapi
import zencad.viewadaptor
import pyservoce.trace
import runpy

import argparse

def main():
	print("__MAIN__", sys.argv)

	parser = argparse.ArgumentParser()
	parser.add_argument("--eventdebug", action="store_true")
	parser.add_argument("--trace", action="store_true")
	parser.add_argument("--mainonly", action="store_true")
	parser.add_argument("--replace", action="store_true")
	parser.add_argument("--widget", action="store_true")
	parser.add_argument("paths", type=str, nargs="*", help="runned file")
	pargs = parser.parse_args()
	
	zencad.shower.__ZENCAD_EVENT_DEBUG__ = pargs.eventdebug
	pyservoce.trace.__TRACE__ = pargs.trace
	zencad.shower.__TRACE__ = pargs.trace
	zencad.viewadaptor.__TRACE__ = pargs.trace
	
	if len(pargs.paths) == 0:
	    path = os.path.join(zencad.exampledir, "helloworld.py")
	else:
	    path = os.path.join(os.getcwd(), pargs.paths[0])
	
	directory = os.path.dirname(path)
	os.chdir(directory)
	sys.path.append(directory)
	
	zencad.showapi.SHOWMODE = "makeapp"

	#if "ZENCAD_MODE" in os.environ:
	#if os.environ["ZENCAD_MODE"] == "MAINONLY":
	if pargs.mainonly:
		zencad.showapi.SHOWMODE = "mainonly"
		return zencad.showapi.show()

	#if os.environ["ZENCAD_MODE"] == "REPLACE_WINDOW":
	if pargs.replace:
		zencad.showapi.SHOWMODE = "replace"

	if pargs.widget:
		zencad.showapi.SHOWMODE = "widget"

	runpy.run_path(path, run_name="__main__")

if __name__ == "__main__":
	main()

# parser = argparse.ArgumentParser()
# parser.add_argument("--application", action='store_true')
# parser.add_argument("--view", action='store_true')
# parser.add_argument("--viewadapter", action='store_true')
# parser.add_argument("--bound-apino")
# parser.add_argument("--bound-wid")
# parser.add_argument("--bound-pid")
# parser.add_argument("--path")
# pargs = parser.parse_args()
#
# if pargs.application:
# 	zencad.application.start_application(bound = (pargs.bound_apino, pargs.bound_wid, pargs.bound_pid, pargs.path))
#
# elif pargs.viewadapter:
# 	zencad.unbound.start_viewadapter_unbounded(apino=pargs.bound_apino, path=pargs.path)
#
# else:
# 	zencad.showapi.mode = "appv1"
# 	path = os.path.join(zencad.exampledir, "helloworld.py")
# 	os.chdir(zencad.exampledir)
# 	sys.path.append(zencad.exampledir)
# 	runpy.run_path(path, run_name="__main__")
