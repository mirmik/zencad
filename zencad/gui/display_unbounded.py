import sys
import io
import os
import time
import subprocess
import runpy
import json

from OCC.Display.backend import load_pyqt5, load_backend
from OCC.Display.backend import get_qt_modules

from zencad.util import print_to_stderr

if not load_pyqt5():
	print("pyqt5 required to run this test")
	sys.exit()

load_backend("qt-pyqt5")
QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()
QtCore.QLoggingCategory.setFilterRules('qt.qpa.xcb=false')

from zencad.gui.display import DisplayWidget
from zencad.gui.communicator import Communicator
from zencad.gui.retransler import ConsoleRetransler


def start_worker(path, sleeped=False, need_prescale=False, session_id=0, size=None):
	prescale = "--prescale" if need_prescale else ""
	sleeped = "--sleeped" if sleeped else ""
	sizestr = "--size {},{}".format(size.width(), size.height()) if size is not None else ""
	interpreter = sys.executable

	cmd = f'{interpreter} -m zencad "{path}" --unbound {prescale} {sleeped} {sizestr}'

	try:
		subproc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE, 
			close_fds=True)
		return subproc
	except OSError as ex:
		print("Warn: subprocess.Popen finished with exception", ex)
		raise ex

def start_unbounded_worker(path, need_prescale, size, sleeped=False, ):
	subproc = start_worker(
		path=path, 
		sleeped=sleeped, 
		need_prescale=need_prescale, 
		size=size)

	stdout = io.TextIOWrapper(subproc.stdout, line_buffering=True)
	stdin = io.TextIOWrapper(subproc.stdin, line_buffering=True)

	communicator = Communicator(ifile=stdout, ofile=stdin)
	communicator.subproc = subproc

	return communicator


COMMUNICATOR = None # используется только в этом файле
PRESCALE_SIZE = None
BIND_MODE = True
def unbound_worker_exec(path, prescale, size, 
	no_communicator_pickle=False,
	sleeped = False):
	global COMMUNICATOR, PRESCALE_SIZE
	QAPP = QtWidgets.QApplication([])

	PRESCALE_SIZE = size

	# Переопределяем дескрипторы, чтобы стандартный поток вывода пошёл
	# через ретранслятор. Теперь все консольные сообщения будуут обвешиваться 
	# тегами и поступать на коммуникатор.
	retransler = ConsoleRetransler(sys.stdout)
	retransler.start()

	# Коммуникатор будет слать сообщения на скрытый файл, 
	# тоесть, на истинный stdout
	COMMUNICATOR = Communicator(
		ifile=sys.stdin, ofile=retransler.new_file,
		no_communicator_pickle=no_communicator_pickle)

	# Показываем ретранслятору его коммуникатор.
	retransler.set_communicator(COMMUNICATOR)

	if sleeped:
		# Спящий процесс оптимизирует время загрузки скрипта.
		# этот процесс повисает в цикле чтения и дожидается,
		# пока ему не передадут задание на выполнение.
		# оптимизация достигается за счёт предварительной загрузки библиотек. 
		dct0 = json.loads( COMMUNICATOR.simple_read() ) # set_oposite_pid
		dct1 = json.loads( COMMUNICATOR.simple_read() ) # unwait

		COMMUNICATOR.declared_opposite_pid = int(dct0["data"])
		path = dct1["path"]
		PRESCALE_SIZE = (int(a) for a in dct1["size"].split(","))

	COMMUNICATOR.start_listen()

	# Устанавливаем флаг в модуль showapi, чтобы процедура show
	# вернула нам управление в функцию unbound_worker_bottom_half.
	import zencad.showapi
	zencad.showapi.UNBOUND_MODE = True

	# Меняем директорию, чтобы скрипт мог подключать зависимые модули.
	directory = os.path.dirname(os.path.abspath(path))
	os.chdir(directory)
	sys.path.append(directory)

	# Совершив подготовительные процедуры, запускаем скрипт.
	runpy.run_path(path, run_name="__main__")

def unbound_worker_bottom_half(scene):
	"""Вызывается из showapi"""

	display = DisplayWidget(
		bind_mode=True, 
		communicator=COMMUNICATOR,
		init_size = PRESCALE_SIZE)
	display.attach_scene(scene)

	if BIND_MODE:
		COMMUNICATOR.send({
			"cmd":"bindwin", 
			"id":int(display.winId()), 
			"pid":os.getpid(), 
		})

	display.show()
	time.sleep(0.05)

	QtWidgets.QApplication.instance().exec()

def spawn_sleeped_worker():
	return start_unbounded_worker(
		path="", 
		need_prescale=False, 
		size=QtCore.QSize(0,0), 
		sleeped=True)