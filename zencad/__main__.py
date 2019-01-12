#!/usr/bin/python3
#coding:utf-8

import argparse
import zencad
import zencad.application
import zencad.showapi
import runpy

print("zencad main file")

parser = argparse.ArgumentParser()
parser.add_argument("--application", action='store_true')
parser.add_argument("--view")
parser.add_argument("--bound-apino")
parser.add_argument("--bound-wid")
parser.add_argument("--bound-pid")
pargs = parser.parse_args()

if pargs.application:
	zencad.application.start_application(bound = (pargs.bound_apino, pargs.bound_wid, pargs.bound_pid))

elif pargs.view:
	path = pargs.view
	zencad.showapi.mode = "view"
	runpy.run_path(path, run_name="__main__")
