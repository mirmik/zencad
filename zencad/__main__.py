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
import subprocess

__MAIN_TRACE__ = False

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
	parser.add_argument("--nodaemon", action="store_true")
	parser.add_argument("--tgtpath")
	parser.add_argument("--session_id", type=int, default=0)
	parser.add_argument("paths", type=str, nargs="*", help="runned file")
	pargs = parser.parse_args()

	trace(pargs)

	# Режим работы программы, в котором создаётся gui с предоткрытым файлом.
	# Используется в том числе для внутренней работы.	
	# TODO: переименовать режим.
	if pargs.mainonly:
		if pargs.tgtpath == None:
			print("Error: mainonly mode without tgtpath")
			exit(0)

		return zencad.gui.application.start_main_application(pargs.tgtpath, display_mode=True)

	if pargs.sleeped:
		# Эксперементальная функциональность для ускорения обновления модели.

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

		MAIN_COMMUNICATOR = zencad.gui.communicator.NoQtCommunicator(
			ipipe=3)
		MAIN_COMMUNICATOR.start_listen()
		MAIN_COMMUNICATOR.naive_connect(handle)
		print("SLEEPED_ARMED")
		MAIN_COMMUNICATOR.wait()
		print("SLEEPED UNSLEEP")

		while flag is False:
			pass
		print("SLEEPED_UNFLAGED")


	if len(pargs.paths) == 0 and not pargs.sleeped:
		# Если программа вызывается без указания файла, создаём gui. 
		# Режим презентации указывает gui, что оно предоставлено само себе
		# и ему следует развлечь публику самостоятельно, не ожидая бинда виджета.
		#thr = multiprocessing.Process(target=lambda:)
		#thr.daemon = True
		#thr.start()
		if pargs.nodaemon:
			zencad.gui.application.start_main_application(presentation=True)
		else:
			# Windows?
			subprocess.Popen("nohup python3 -m zencad --nodaemon > /dev/null 2>&1&", shell=True, stdout=None, stderr=None)
		
	else:
		# Режим работы, когда указан файл.
		# Политика такова, что начало исполняется вычисляемый 
		# скрипт, а потом, после вызова zencad.show,
		# применяются указанные варианты вызова.
		# информация отсюда транслируется функции show
		# через глобальные переменные.

		path = os.path.join(os.getcwd(), pargs.paths[0])
		zencad.showapi.EXECPATH = path
	
		# Устанавливаем рабочей директорией дирректорию,
		# содержащую целевой файл.
		# TODO: Возможно, так делать нужно только
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
		# Информация об окне передаётся основному процессу через пайп.
		if pargs.replace:
			zencad.showapi.PRESCALE = pargs.prescale
			zencad.showapi.SESSION_ID = int(pargs.session_id)
			zencad.showapi.SHOWMODE = "replace"

			zencad.application.MAIN_COMMUNICATOR = zencad.gui.communicator.Communicator(
				ipipe=ipipe, opipe=opipe)
			zencad.application.MAIN_COMMUNICATOR.start_listen()

			o, i = os.pipe()
			f = os.fdopen(o)

			sys.stdout = f
	
		# Режим работы в котором виджет работает отдельно и не биндится в gui:
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
