#!/usr/bin/python3
#coding:utf-8

import os
import sys
import argparse
import zencad
import zencad.application
import zencad.showapi
import zencad.unbound
import runpy

parser = argparse.ArgumentParser()
parser.add_argument("--application", action='store_true')
parser.add_argument("--view", action='store_true')
parser.add_argument("--viewadapter", action='store_true')
parser.add_argument("--bound-apino")
parser.add_argument("--bound-wid")
parser.add_argument("--bound-pid")
parser.add_argument("--path")
pargs = parser.parse_args()

if pargs.application:
	zencad.application.start_application(bound = (pargs.bound_apino, pargs.bound_wid, pargs.bound_pid, pargs.path))

elif pargs.viewadapter:
	zencad.unbound.start_viewadapter_unbounded(apino=pargs.bound_apino, path=pargs.path)

else:
	zencad.showapi.mode = "appv1"
	path = os.path.join(zencad.exampledir, "helloworld.py")
	os.chdir(zencad.exampledir)
	sys.path.append(zencad.exampledir)
	runpy.run_path(path, run_name="__main__")
