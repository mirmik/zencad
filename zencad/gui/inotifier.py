import os
import time
import threading

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class InotifyThread(QThread):
    """InotifyThread следит за переданным ему списком файлов
    и бросает сигналы в случае обноружения модификации одного из файлов"""

    changed = pyqtSignal()

    class Record:
        def __init__(self, path, mtime):
            self.path = path
            self.mtime = mtime

    def __init__(self, parent):
        QThread.__init__(self, parent)
        self._lock = threading.Lock()
        self._control_lock = threading.Lock()
        self.emit_time = time.time()
        self.stop_token = False

        self.targets_list = {}

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        if not self.isRunning():
            self.start()

        self._lock.release()

    def control_lock(self):
        self._control_lock.acquire()

    def control_unlock(self):
        if not self.isRunning():
            self.start()

        if self._control_lock.locked():
            self._control_lock.release()

    def add_target(self, path):
        self.lock()
        mtime = os.stat(path).st_mtime
        self.targets_list[path] = self.Record(path, mtime)
        self.unlock()

    def del_target(self, path):
        self.lock()
        if path in self.targets_list:
            del self.targets_list[path]
        else:
            raise Exception("Try to del unregistred path")
        self.unlock()

    def clear(self):
        self.lock()
        self.targets_list.clear()
        self.unlock()

    def stop(self):
        self.stop_token = True

    def finish(self):
        self.stop_token = True

        # control_lock устанавливается в actions графическим потоком
        # снимается им же при завершении
        self.control_unlock()

    def run(self):
        while 1:
            if self.stop_token:
                return

            # порядок мьютексов важен.
            # пока control_lock захвачен, targets_list можно менять, т.к.
            # lock не захвачен
            self._control_lock.acquire()
            self._lock.acquire()
            try:
                for path, record in self.targets_list.items():
                    if os.stat(record.path).st_mtime != record.mtime:
                        if time.time() - self.emit_time > 0.75:
                            self.last_mtime = os.stat(path).st_mtime
                            self.changed.emit()
                            self.emit_time = time.time()
                            break
            except FileNotFoundError:
                pass

            self._lock.release()
            self._control_lock.release()

            time.sleep(0.01)
