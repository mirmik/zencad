#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import zencad
import zencad.showapi
import zencad.gui.viewadaptor
import pyservoce.trace
import runpy

import pickle
import sys, traceback
import argparse

print(sys.argv)

__MAIN_TRACE__ = True

def trace(*argv, **kwars):
	if __MAIN_TRACE__: print(*argv, **kwars)

def main():
	trace("__MAIN__", sys.argv)

	parser = argparse.ArgumentParser()
	parser.add_argument("--mainonly", action="store_true")
	parser.add_argument("--replace", action="store_true")
	parser.add_argument("--widget", action="store_true")
	parser.add_argument("--prescale", action="store_true")
	parser.add_argument("--sleeped", action="store_true")
	parser.add_argument("--tgtpath")
	parser.add_argument("--session_id", type=int, default=0)
	parser.add_argument("paths", type=str, nargs="*", help="runned file")
	pargs = parser.parse_args()

	trace(pargs)

	# Режим работы программы, в котором создаётся gui.
	# Используется в том числе для внутренней работы.	
	if pargs.mainonly:
		if pargs.tgtpath == None:
			print("Error: mainonly mode without tgtpath")
			exit(0)

		return zencad.unbound.application.start_main_application(pargs.tgtpath)

	if pargs.sleeped:
		flag = False
		MAIN_COMMUNICATOR = None
		def handle(data):
			nonlocal flag
			data = pickle.loads(data)
			print("HANDLE", data)
			pargs.prescale = data["need_prescale"]
			pargs.paths = [data["path"]]
			flag=True
			MAIN_COMMUNICATOR.stop_listen()

		MAIN_COMMUNICATOR = zencad.unbound.communicator.NoQtCommunicator(
			ipipe=3)
		MAIN_COMMUNICATOR.start_listen()
		MAIN_COMMUNICATOR.naive_connect(handle)
		print("SLEEPED_ARMED")
		MAIN_COMMUNICATOR.wait()
		print("SLEEPED UNSLEEP")

		while flag is False:
			pass
		print("SLEEPED_UNFLAGED")


	# Если программа вызывается без указания файла, 
	# Открываем helloworld
	# TODO: На самом деле нужно создавать временный файл.
	if len(pargs.paths) == 0 and not pargs.sleeped:
		#zencad.showapi.SHOWMODE = "presentation"
		#path = os.path.join(zencad.exampledir, "helloworld.py")
		zencad.unbound.application.start_main_application(presentation=True)
		return

	else:
		zencad.showapi.SHOWMODE = "makeapp"
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
		#zencad.showapi.SHOWMODE = "makeapp"
	
		# Специальный режим, устанавливаемый GUI при загрузке скрипта.
		# Делает ребинд модели в уже открытом gui.
		if pargs.replace:
			zencad.showapi.PRESCALE = pargs.prescale
			#zencad.showapi.SLEEPED = pargs.sleeped
			zencad.showapi.SESSION_ID = int(pargs.session_id)
			zencad.showapi.SHOWMODE = "replace"
	
		# Режим работы для теста виджета:
		if pargs.widget:
			zencad.showapi.SHOWMODE = "widget"

		try:
			runpy.run_path(path, run_name="__main__")
		except Exception as ex:
			print("Exception in runned script: {}".format(ex))
			ex_type, ex, tb = sys.exc_info()
			traceback.print_tb(tb)
	
	trace("AFTER RUNPY")

if __name__ == "__main__":
	main()
