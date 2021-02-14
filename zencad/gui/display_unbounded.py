import sys
import io
import subprocess
import runpy

from OCC.Display.backend import load_pyqt5, load_backend
from OCC.Display.backend import get_qt_modules

from zencad.util import print_to_stderr

if not load_pyqt5():
	print("pyqt5 required to run this test")
	sys.exit()

load_backend("qt-pyqt5")
QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()

from zencad.gui.display import DisplayWidget
from zencad.gui.communicator import Communicator
from zencad.gui.retransler import ConsoleRetransler

from PyQt5 import QtCore, QtGui, QtOpenGL, QtWidgets

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
def unbound_worker_exec(path, prescale, size, no_communicator_pickle=False):
	global COMMUNICATOR
	QAPP = QtWidgets.QApplication([])

	# Переопределяем дескрипторы, чтобы стандартный поток вывода пошёл
	# через ретранслятор. Теперь все консольные сообщения будуут обвешиваться 
	# тегами и поступать на коммуникатор.
	retransler = ConsoleRetransler(sys.stdout)
	retransler.start()

	# Коммуникатор будет слать сообщения на скрытый файл, 
	# тоесть, на истинный stdout
	COMMUNICATOR = Communicator(
		ifile=sys.stdin, ofile=retransler.new_file,
		no_communicator_pickle = no_communicator_pickle)

	# Показываем ретранслятору его коммуникатор.
	retransler.set_communicator(COMMUNICATOR)

	COMMUNICATOR.start_listen()

	# Устанавливаем флаг в модуль showapi, чтобы процедура show
	# вернула нам управление в функцию unbound_worker_bottom_half.
	import zencad.showapi
	zencad.showapi.UNBOUND_MODE = True

	# Совершив подготовительные процедуры, запускаем скрипт.
	runpy.run_path(path, run_name="__main__")

def unbound_worker_bottom_half(scene):
	"""Вызывается из showapi"""

	display = DisplayWidget(bind_mode=True, communicator=COMMUNICATOR)
	display.attach_scene(scene)
	display.show()

	return QtWidgets.QApplication.instance().exec()