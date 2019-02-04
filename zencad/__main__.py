#!/usr/bin/env python3
#coding:utf-8

import os
import sys
import zencad
import zencad.shower
import zencad.showapi
import runpy

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--eventdebug", action='store_true')
pargs = parser.parse_args()

zencad.shower.__ZENCAD_EVENT_DEBUG__ = pargs.eventdebug

path = os.path.join(zencad.exampledir, "helloworld.py")
os.chdir(zencad.exampledir)
sys.path.append(zencad.exampledir)
zencad.showapi.mode = "app_fullview"
runpy.run_path(path, run_name="__main__")

#parser = argparse.ArgumentParser()
#parser.add_argument("--application", action='store_true')
#parser.add_argument("--view", action='store_true')
#parser.add_argument("--viewadapter", action='store_true')
#parser.add_argument("--bound-apino")
#parser.add_argument("--bound-wid")
#parser.add_argument("--bound-pid")
#parser.add_argument("--path")
#pargs = parser.parse_args()
#
#if pargs.application:
#	zencad.application.start_application(bound = (pargs.bound_apino, pargs.bound_wid, pargs.bound_pid, pargs.path))
#
#elif pargs.viewadapter:
#	zencad.unbound.start_viewadapter_unbounded(apino=pargs.bound_apino, path=pargs.path)
#
#else:
#	zencad.showapi.mode = "appv1"
#	path = os.path.join(zencad.exampledir, "helloworld.py")
#	os.chdir(zencad.exampledir)
#	sys.path.append(zencad.exampledir)
#	runpy.run_path(path, run_name="__main__")
