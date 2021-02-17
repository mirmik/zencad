from zencad.gui.retransler import ConsoleRetransler
from zencad.gui.communicator import Communicator
from zencad.gui.display import DisplayWidget
import sys
import io
import os
import time
import subprocess
import runpy
import signal
import json

from zencad.util import print_to_stderr

from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL
QtCore.QLoggingCategory.setFilterRules('qt.qpa.xcb=false')


def start_worker(path, sleeped=False, need_prescale=False, session_id=0, size=None):
    prescale = "--prescale" if need_prescale else ""
    sleeped = "--sleeped" if sleeped else ""
    sizestr = "--size {},{}".format(size.width(),
                                    size.height()) if size is not None else ""
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


COMMUNICATOR = None
RETRANSLER = None
PRESCALE_SIZE = None
BIND_MODE = True


def qt_sigterm_handle(a, b):
    sys.exit()


def qt_setup_signal_handling():
    from zencad.util import print_to_stderr
    signal.signal(signal.SIGTERM, qt_sigterm_handle)
    signal.signal(signal.SIGINT, qt_sigterm_handle)


def unbound_worker_exec(path, prescale, size,
                        no_communicator_pickle=False,
                        sleeped=False):
    global COMMUNICATOR, PRESCALE_SIZE, RETRANSLER
    QAPP = QtWidgets.QApplication([])
    qt_setup_signal_handling()

    PRESCALE_SIZE = size

    # Переопределяем дескрипторы, чтобы стандартный поток вывода пошёл
    # через ретранслятор. Теперь все консольные сообщения будуут обвешиваться
    # тегами и поступать на коммуникатор.
    RETRANSLER = ConsoleRetransler(sys.stdout)
    RETRANSLER.start()

    # Коммуникатор будет слать сообщения на скрытый файл,
    # тоесть, на истинный stdout
    COMMUNICATOR = Communicator(
        ifile=sys.stdin, ofile=RETRANSLER.new_file,
        no_communicator_pickle=no_communicator_pickle)

    # Показываем ретранслятору его коммуникатор.
    RETRANSLER.set_communicator(COMMUNICATOR)

    if sleeped:
        # Спящий процесс оптимизирует время загрузки скрипта.
        # этот процесс повисает в цикле чтения и дожидается,
        # пока ему не передадут задание на выполнение.
        # оптимизация достигается за счёт предварительной загрузки библиотек.
        try:
            dct0 = json.loads(COMMUNICATOR.simple_read())  # set_oposite_pid
            dct1 = json.loads(COMMUNICATOR.simple_read())  # unwait
        except Exception as ex:
            print_to_stderr("sleeped thread finished with exception")
            print_to_stderr(ex)
            sys.exit()

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
