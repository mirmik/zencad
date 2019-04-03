#!/usr/bin/env python3

import threading
import os
import sys
import time
from signal import SIGTERM

from zencad.application import MainWindow
from zencad.viewadaptor import GeometryWidget
import zencad.opengl
import zencad.rpc

import zencad.spawn

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal


def start_unbound(scn, animate=None):
    import zencad.application
    import zencad.viewadapter

    app = QApplication([])
    zencad.opengl.init_opengl()

    wdg = zencad.viewadapter.start_viewadapter(scn, animate)
    apino = wdg.get_apino()
    wid = wdg.get_wid()

    module_path = zencad.moduledir
    thr = threading.Thread(
        target=lambda: os.system(
            "python3 {} --application --bound-apino {} --bound-wid {} --bound-pid {} --path {}".format(
                os.path.join(module_path, "__main__.py"),
                apino,
                wid,
                os.getpid(),
                sys.argv[0],
            )
        )
    )
    thr.start()

    def stopworld():
        wdg.stop()
        app.quit()

    wdg.ctransler.stopworld_signal.connect(stopworld)
    wdg.show()
    return app.exec()


def start_viewadapter_unbound(self, path):
    ctransler = zencad.rpc.ServerTransler(self)

    module_path = zencad.moduledir
    cmd = "python3 {} --viewadapter --bound-apino {} --path {} > /dev/null".format(
        os.path.join(module_path, "__main__.py"), ctransler.get_apino(), path
    )
    thr = threading.Thread(target=lambda: os.system(cmd))
    thr.start()

    return ctransler


def start_viewadapter_unbounded(path, apino):
    import zencad.viewadapter
    import runpy

    os.chdir(os.path.dirname(path))
    sys.path.insert(0, os.path.dirname(path))

    class runner(QThread):
        def run(self):
            runpy.run_path(path, run_name="__main__")

    # class console_retransler(QThread):
    # 	ctransler_send = pyqtSignal(str)
    # 	def __init__(self):
    # 		QThread.__init__(self)
    # 		r,w = os.pipe()
    # 		d = os.dup(1)
    # 		os.close(1)
    # 		os.dup2(w, 1)
    # 		self.d = d
    # 		self.r = r
    #
    # 	def run(self):
    # 		while 1:
    # 			data = os.read(self.r, 512)
    # 			os.write(self.d, data)
    # 			self.ctransler_send.emit(data.decode("utf-8"))

    class stdout_proxy:
        def __init__(self, stdout, wdg):
            self.stdout = stdout
            self.wdg = wdg

        def write(self, data):
            # self.stdout.write(data)
            self.wdg.ctransler.log(data)

        def flush(self):
            self.stdout.flush()

    app = QApplication([])
    zencad.opengl.init_opengl()
    zencad.showapi.mode = "viewadapter"

    wdg = zencad.viewadapter.start_viewadapter(None, connect=apino)
    sys.stdout = stdout_proxy(sys.stdout, wdg)

    globals()["__SYNCVAR__"] = None

    def setsyncvar():
        globals()["__SYNCVAR__"] = True

    def stopworld():
        wdg.stop()
        app.quit()

    wdg.ctransler.sync_signal.connect(setsyncvar)
    wdg.ctransler.stopworld_signal.connect(stopworld)

    globals()["__WIDGET__"] = wdg

    runner = runner()
    runner.start()
    app.exec()


def unbound_show_adapter(scn):
    wdg = globals()["__WIDGET__"]
    wdg.scene = scn

    sys.stdout.write("render scene...")
    wdg.init_viewer()
    print("ok")

    def showready():
        wdg.ctransler.send("readytoshow", args=(int(wdg.winId()),))

        while globals()["__SYNCVAR__"] == None:
            time.sleep(0.01)

    wdg.showready_signal.connect(showready)
    wdg.show()


# def application_starter(pid, r_id, w_sync, tpl):
# 	from zencad.application import MainWindow
#
# 	#init noqt context
# 	cr1, cw1 = os.pipe()
# 	cr2, cw2 = os.pipe()
# 	zencad.spawn.make_clean_spawner(cr1, cw2)
# 	clean_spawner_ctransler = zencad.rpc.NoQtTransler(cr2, cw1)
#
# 	#get winid from creator thread
# 	winid = int(os.read(r_id, 512).decode("utf-8"))
# 	os.close(r_id)
#
# 	app = QApplication([])
# 	ctransler = zencad.rpc.ApplicationNode(*tpl)
# 	print("create mainwindow")
# 	mw = MainWindow()
# 	mw.clean_spawner_ctransler = clean_spawner_ctransler
#
# 	def stopworld():
# 		print("stopworld(application)")
# 		mw.broadcast_send("stopworld")
# 		clean_spawner_ctransler.stop()
# 		ctransler.stop()
# 		app.quit()
#
# 	mw.add_view_by_id(winid, ctransler, pid)
# 	mw.show()
# 	os.write(w_sync, "sync".encode("utf-8"))
# 	os.close(w_sync)
#
# 	print("app.exec()")
# 	app.lastWindowClosed.connect(stopworld)
# 	app.exec()


# class update_loop(QThread):
# 	def __init__(self, parent, updater_function, wdg, pause_time=0.01):
# 		QThread.__init__(self, parent)
# 		self.updater_function = updater_function
# 		self.wdg = wdg
# 		self.pause_time = pause_time
#
# 	def run(self):
# 		while 1:
# 			ensave = zencad.lazy.encache
# 			desave = zencad.lazy.decache
# 			onplace = zencad.lazy.onplace
# 			diag = zencad.lazy.diag
# 			if self.wdg.inited:
# 				zencad.lazy.encache = False
# 				zencad.lazy.decache = False
# 				zencad.lazy.onplace = True
# 				zencad.lazy.diag = False
# 				self.updater_function(self.wdg)
# 				zencad.lazy.onplace = onplace
# 				zencad.lazy.encache = ensave
# 				zencad.lazy.decache = desave
# 				zencad.lazy.diag = diag
# 				time.sleep(self.pause_time)
#
# def animate_stub(wdg):
# 	wdg.view.redraw()
#
# def start_unbound(scn, animate=None):
# 	pid = os.getpid()
# 	r_id, w_id = os.pipe()
# 	r_sync, w_sync = os.pipe()
#
# 	cr1, cw1 = os.pipe()
# 	cr2, cw2 = os.pipe()
#
# 	ctransler = zencad.rpc.EvaluatorNode(cr1, cw2)
#
# 	appproc = multiprocessing.Process(target = application_starter, args=(pid, r_id, w_sync, (cr2, cw1)))
# 	appproc.start()
#
#
# 	app = QApplication([])
# 	zencad.opengl.init_opengl()
# 	disp = GeometryWidget(scn)
# 	os.write(w_id, str(int(disp.winId())).encode("utf-8"))
# 	os.close(w_id)
# 	os.read(r_sync, 512)
# 	os.close(r_sync)
#
# 	def stopworld():
# 		print("stopworld(starter)")
# 		ctransler.stop()
# 		app.quit()
#
# 	ctransler.stopWorldSignal.connect(stopworld)
# 	ctransler.actionCenteringSignal.connect(disp.action_centering)
# 	ctransler.actionAutoscaleSignal.connect(disp.action_autoscale)
# 	ctransler.actionResetSignal.connect(disp.action_reset)
#
# 	if animate != None:
# 		thr = update_loop(disp, animate, disp)
# 		thr.start()
# 	else:
# 		#thr = update_loop(disp, animate_stub, disp)
# 		#thr.start()
# 		pass
#
# 	disp.show()
# 	app.exec()
#
#
# def start_self(scn):
# 	app = QApplication([])
# 	#zencad.opengl.init_opengl()
# 	disp = GeometryWidget(scn)
# 	disp.show()
# 	app.exec()
#
#
# def start_self(scn):
# 	app = QApplication([])
# 	zencad.opengl.init_opengl()
# 	disp = GeometryWidget(scn)
# 	disp.show()
# 	app.exec()#
