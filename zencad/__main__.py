#!/usr/bin/env python3
# coding:utf-8

import os
import sys
import zencad
import zencad.showapi
import zencad.gui.application
import zencad.gui.viewadaptor
import zencad.gui.retransler
import zencad.gui.mainwindow
import pyservoce.trace
import runpy

import pickle
import sys, traceback
import argparse
import subprocess
import threading
import multiprocessing
import base64
import psutil
import signal

from zencad.util import print_to_stderr

CONSOLE_RETRANS = True
__MAIN_TRACE__ = False

STDOUT_FILENO = zencad.gui.application.STDOUT_FILENO
STDIN_FILENO = zencad.gui.application.STDIN_FILENO

def trace(*args):
	if __MAIN_TRACE__: 
		sys.stderr.write(str(args))
		sys.stderr.write("\r\n")
		sys.stderr.flush()

def finish_procedure():
	trace("MAIN FINISH")

	trace("MAIN: Wait childs ...")
	trace("MAIN:  list of threads: ", threading.enumerate())

	if zencad.gui.application.CONSOLE_RETRANS_THREAD:
		zencad.gui.application.CONSOLE_RETRANS_THREAD.finish()
	
	def on_terminate(proc):
		trace("process {} finished with exit code {}".format(proc, proc.returncode))
	
	procs = psutil.Process().children()
	psutil.wait_procs(procs, callback=on_terminate)
	#for p in procs:
	#    p.terminate()
	#gone, alive = psutil.wait_procs(procs, timeout=3, callback=on_terminate)
	#for p in alive:
	#    p.kill()
	trace("MAIN: Wait childs ... OK")

def do_main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--info", action="store_true")
	parser.add_argument("--mainonly", action="store_true")
	parser.add_argument("--replace", action="store_true")
	parser.add_argument("--widget", action="store_true")
	parser.add_argument("--prescale", action="store_true")
	parser.add_argument("--sleeped", action="store_true")
	parser.add_argument("--nodaemon", action="store_true")
	parser.add_argument("--disable-show", action="store_true")
	parser.add_argument("--tgtpath")
	parser.add_argument("--debug", action="store_true")
	parser.add_argument("--debugcomm", action="store_true")
	parser.add_argument("--session_id", type=int, default=0)
	parser.add_argument("paths", type=str, nargs="*", help="runned file")
	pargs = parser.parse_args()

	if pargs.debug:
		global __MAIN_TRACE__
		zencad.gui.application.__DEBUG_MODE__ = True
		__MAIN_TRACE__ = True
		zencad.gui.application.__TRACE__ = True
		zencad.gui.retransler.__RETRANSLER_TRACE__ = True
		zencad.gui.viewadaptor.__TRACE__ = True
		zencad.gui.mainwindow.__TRACE__ = True

	if pargs.debugcomm:
		zencad.gui.communicator.__TRACE__ = True

	trace("__MAIN__", sys.argv)
	trace(pargs)

	if pargs.info:
		print(zencad.moduledir)
		return

	pargs.nodaemon = True

	# Режим работы программы, в котором создаётся gui с предоткрытым файлом.
	# Используется в том числе для внутренней работы.	
	# TODO: переименовать режим.
	if pargs.mainonly:
		if pargs.tgtpath == None:
			print_to_stderr("Error: mainonly mode without tgtpath")
			exit(0)

		zencad.gui.application.start_main_application(pargs.tgtpath, display_mode=True, console_retrans=True)	
		return

	if pargs.replace and CONSOLE_RETRANS:
		# Теперь можно сделать поток для обработки данных, которые программа собирается 
		# посылать в stdout
		zencad.gui.application.CONSOLE_RETRANS_THREAD = zencad.gui.retransler.console_retransler()
		zencad.gui.application.CONSOLE_RETRANS_THREAD.start()

	if pargs.sleeped:
		# Эксперементальная функциональность для ускорения обновления модели. 
		# Процесс для обновления модели создаётся заранее и ждёт, пока его пнут со стороны сервера.
		data = os.read(zencad.gui.application.STDIN_FILENO, 512)
		try:
			data = pickle.loads(base64.decodestring(data))
		except:
			print_to_stderr("Unpickle error", data)
			exit(0)			

		if "cmd" in data and data["cmd"] == "stopworld":
			return

		try:
			pargs.prescale = data["need_prescale"]
			pargs.paths = [data["path"]]
		except:
			print_to_stderr("Unpickle error_2", data)
			exit(0)			

	if pargs.replace and CONSOLE_RETRANS:

		# Теперь можно сделать поток для обработки данных, которые программа собирается 
		# посылать в stdout
		zencad.gui.application.MAIN_COMMUNICATOR = zencad.gui.communicator.Communicator(
			ipipe=zencad.gui.application.STDIN_FILENO, opipe=3)
		zencad.gui.application.MAIN_COMMUNICATOR.start_listen()
		zencad.gui.application.MAIN_COMMUNICATOR.send({"cmd":"clientpid", "pid":int(os.getpid())})
	


	if len(pargs.paths) == 0 and not pargs.sleeped:
		# Если программа вызывается без указания файла, создаём gui. 
		# Режим презентации указывает gui, что оно предоставлено само себе
		# и ему следует развлечь публику самостоятельно, не ожидая бинда виджета.
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
	
		# Режим работы в котором виджет работает отдельно и не биндится в gui:
		if pargs.widget:
			zencad.showapi.SHOWMODE = "widget"

		if pargs.disable_show:
			zencad.showapi.SHOWMODE = "noshow"

		try:
			runpy.run_path(path, run_name="__main__")
		except Exception as ex:
			print("Error: {}".format(ex))
			ex_type, ex, tb = sys.exc_info()
			traceback.print_tb(tb)
	
	trace("AFTER RUNPY")

def main():
	do_main()
	finish_procedure()
	trace("EXIT")
	exit(0)

if __name__ == "__main__":
	zencad.util.set_process_name("zencad")
	main()

	
