import sys
import io
import os
import time
import traceback
import subprocess
import runpy
import signal
import json

from zencad.frame.retransler import ConsoleRetransler
from zencad.frame.communicator import Communicator
from zencad.frame.client import Client

from zencad.gui.display import DisplayWidget
from zencad.frame.finisher import setup_finish_handler, setup_interrupt_handlers

from zencad.frame.util import print_to_stderr
from zencad.lazifier import install_evalcahe_notication

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL

from zencad.configuration import Configuration
if Configuration.FILTER_QT_WARNINGS:
    QtCore.QLoggingCategory.setFilterRules('qt.qpa.xcb=false')


def start_worker(path, sleeped=False, need_prescale=False, session_id=0, size=None):
    prescale = "--prescale" if need_prescale else ""
    sleeped = "--sleeped" if sleeped else ""
    sizestr = f"--size {size[0]},{size[1]}" if size is not None else ""
    interpreter = sys.executable

    cmd = f'{interpreter} -m zencad "{path}" --unbound {prescale} {sleeped} {sizestr}'

    try:
        subproc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                   close_fds=True)
        return subproc
    except OSError as ex:
        print("Warn: subprocess.Popen finished with exception", ex)
        raise ex


def start_unbounded_worker(path, need_prescale, size, sleeped=False):
    subproc = start_worker(
        path=path,
        sleeped=sleeped,
        need_prescale=need_prescale,
        size=size)

    stdout = io.TextIOWrapper(subproc.stdout, line_buffering=True)
    stdin = io.TextIOWrapper(subproc.stdin, line_buffering=True)

    communicator = Communicator(ifile=stdout, ofile=stdin)
    client = Client(communicator=communicator, subprocess=subproc)

    return client


COMMUNICATOR = None
RETRANSLER = None
PRESCALE_SIZE = None
BIND_MODE = True


def unbound_worker_exec(path, prescale, size,
                        sleeped=False):
    global COMMUNICATOR, PRESCALE_SIZE, RETRANSLER
    QAPP = QtWidgets.QApplication([])
    PRESCALE_SIZE = size

    # Переопределяем дескрипторы, чтобы стандартный поток вывода пошёл
    # через ретранслятор. Теперь все консольные сообщения будуут обвешиваться
    # тегами и поступать на коммуникатор.
    RETRANSLER = ConsoleRetransler(sys.stdout)
    RETRANSLER.start_listen()

    # Коммуникатор будет слать сообщения на скрытый файл,
    # тоесть, на истинный stdout
    COMMUNICATOR = Communicator(
        ifile=sys.stdin, ofile=RETRANSLER.new_file)

    # Показываем ретранслятору его коммуникатор.
    RETRANSLER.set_communicator(COMMUNICATOR)

    def stop_handler():
        COMMUNICATOR.stop_listen()
        RETRANSLER.stop_listen()

    setup_finish_handler(stop_handler)
    setup_interrupt_handlers()
    
    if sleeped:
        # Спящий процесс оптимизирует время загрузки скрипта.
        # этот процесс повисает в цикле чтения и дожидается,
        # пока ему не передадут задание на выполнение.
        # оптимизация достигается за счёт предварительной загрузки библиотек.
        try:
            data0 = COMMUNICATOR.simple_read()
            data1 = COMMUNICATOR.simple_read()

            if Configuration.COMMUNICATOR_TRACE:
                print_to_stderr("slep", data0)
                print_to_stderr("slep", data1)
            dct0 = json.loads(data0)  # set_oposite_pid
            dct1 = json.loads(data1)  # unwait
        except Exception as ex:
            print_to_stderr("sleeped thread finished with exception")
            print_to_stderr(ex)
            sys.exit()

        COMMUNICATOR.declared_opposite_pid = int(dct0["data"])
        path = dct1["path"]
        PRESCALE_SIZE = list((int(a) for a in dct1["size"].split(",")))

    install_evalcahe_notication(COMMUNICATOR)

    COMMUNICATOR.oposite_clossed.connect(
        QtWidgets.QApplication.instance().quit)

    COMMUNICATOR.start_listen()

    # Устанавливаем флаг в модуль showapi, чтобы процедура show
    # вернула нам управление в функцию unbound_worker_bottom_half.
    import zencad.showapi
    zencad.showapi.UNBOUND_MODE = True

    # Меняем директорию, чтобы скрипт мог подключать зависимые модули.
    path = os.path.abspath(path)
    directory = os.path.dirname(os.path.abspath(path))
    os.chdir(directory)
    sys.path.append(directory)

    # Совершив подготовительные процедуры, запускаем скрипт.
    try:
        runpy.run_path(path, run_name="__main__")
    except Exception as ex:
        tb = traceback.format_exc()
        COMMUNICATOR.send({"cmd": "except", "path":path, "header": repr(ex), "tb": str(tb)})


def unbound_worker_bottom_half(scene):
    """Вызывается из showapi"""

    display = DisplayWidget(
        bind_mode=True,
        communicator=COMMUNICATOR,
        init_size=PRESCALE_SIZE)
    display.attach_scene(scene)

    # todo: почему не внутри?
    COMMUNICATOR.bind_handler(display.external_communication_command)

    if BIND_MODE:
        COMMUNICATOR.send({
            "cmd": "bindwin",
            "id": int(display.winId()),
            "pid": os.getpid(),
        })

    display.show()
    time.sleep(0.05)

    timer = QtCore.QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    QtWidgets.QApplication.instance().exec()


def spawn_sleeped_worker():
    return start_unbounded_worker(
        path="",
        need_prescale=False,
        size=QtCore.QSize(0, 0),
        sleeped=True)
