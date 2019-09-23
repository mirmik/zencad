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

__MAIN_TRACE__ = False

def trace(*argv, **kwars):
	if __MAIN_TRACE__: print(*argv, **kwars)

def main():
	trace("__MAIN__", sys.argv)

	parser = argparse.ArgumentParser()
	parser.add_argument("--mainonly", action="store_true")
	parser.add_argument("--replace", action="store_true")
	parser.add_argument("--widget", action="store_true")
	parser.add_argument("--tgtpath")
	parser.add_argument("paths", type=str, nargs="*", help="runned file")
	pargs = parser.parse_args()

	# Режим работы программы, в котором создаётся gui.
	# Используется в том числе для внутренней работы.	
	if pargs.mainonly:
		if pargs.tgtpath == None:
			print("Error: mainonly mode without tgtpath")
			exit(0)

		return zencad.unbound.application.start_main_application(pargs.tgtpath)

	# Если программа вызывается без указания файла, 
	# Открываем helloworld
	# TODO: На самом деле нужно создавать временный файл.
	if len(pargs.paths) == 0:
	    path = os.path.join(zencad.exampledir, "helloworld.py")
	else:
	    path = os.path.join(os.getcwd(), pargs.paths[0])
	
	# Устанавливаем рабочей директорией дирректорию,
	# содержащую целевой файл.
	# TODO: Вероятнее всего, так делать нужно только
	# при загрузке через GUI. Вынести флаг?
	directory = os.path.dirname(path)
	os.chdir(directory)
	sys.path.append(directory)
	
	# По умолчанию приложение работает в режиме,
	# предполагающем вызов указанного скрипта. 
	# Далее скрипт сам должен создать GUI через showapi.
	zencad.showapi.SHOWMODE = "makeapp"

	# Специальный режим, устанавливаемый GUI при загрузке скрипта.
	# Делает ребинд модели в уже открытом gui.
	if pargs.replace:
		zencad.showapi.SHOWMODE = "replace"

	# Режим работы для теста виджета:
	if pargs.widget:
		zencad.showapi.SHOWMODE = "widget"

	runpy.run_path(path, run_name="__main__")

if __name__ == "__main__":
	main()
