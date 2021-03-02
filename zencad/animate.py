from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import time
import traceback
import sys

import zencad


class AnimationState:
    def __init__(self, widget):
        self.widget = widget
        self.start_time = time.time()
        self.time = time.time()
        self.last_time = time.time()
        self.delta = 0
        self.scene = None

    def timestamp(self, time):
        self.time = time
        self.loctime = time - self.start_time
        self.delta = time - self.last_time
        self.last_time = time


class AnimateThread(QThread):
    after_update_signal = pyqtSignal()

    def __init__(self, widget, updater_function, animate_step=1/100):
        import zenframe

        QThread.__init__(self)
        self.updater_function = updater_function
        #self.parent = widget
        widget.animate_thread = self
        self.wdg = widget
        self.animate_step = animate_step
        self.cancelled = False

        self.state = AnimationState(self.wdg)

        self.after_update_signal.connect(widget.continuous_redraw)

        zenframe.finisher.register_destructor(self, self.finish)

    def finish(self):
        self.cancelled = True
        self.wdg.animate_updated.set()

    def set_animate_step(self, step):
        self.animate_step = step

    def run(self):
        while not self.wdg._inited1:
            time.sleep(0.1)

        self.state.timestamp(time.time())
        self.state.start_time = time.time()

        lasttime = time.time() - self.animate_step
        plantime = time.time()

        while 1:
            try:
                curtime = time.time()
                deltatime = curtime - lasttime
                errtime = plantime - curtime

                if self.cancelled:
                    return

                if errtime > 0:
                    time.sleep(errtime)

                if self.cancelled:
                    return

                lasttime = time.time()

                self.state.timestamp(time.time())
                plantime = plantime + self.animate_step

                ensave = zencad.lazy.encache
                desave = zencad.lazy.decache
                onplace = zencad.lazy.onplace
                diag = zencad.lazy.diag

                zencad.lazy.encache = False
                zencad.lazy.decache = False
                zencad.lazy.onplace = True
                zencad.lazy.diag = False
                self.updater_function(self.state)
                zencad.lazy.onplace = onplace
                zencad.lazy.encache = ensave
                zencad.lazy.decache = desave
                zencad.lazy.diag = diag

                self.wdg.animate_updated.clear()
                if self.cancelled:
                    return

                self.after_update_signal.emit()
                self.wdg.animate_updated.wait()

                if self.cancelled:
                    return
            except:
                print("Error: Exception in animation thread.")
                traceback.print_exc(file=sys.stdout)
                return
