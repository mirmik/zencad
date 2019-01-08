#!/usr/bin/env python3

import multiprocessing
import os
import sys
import time
from signal import SIGTERM

from zencad.application import MainWindow
from zencad.viewadaptor import GeometryWidget
import zencad.opengl
import zencad.rpc

from PyQt5.QtWidgets import QApplication

def application_starter(pid, r_id, w_sync, tpl):
	from zencad.application import MainWindow

	winid = int(os.read(r_id, 512).decode("utf-8"))
	os.close(r_id)

	def kill_parent():
		os.kill(pid, SIGTERM)

	app = QApplication([])
	app.lastWindowClosed.connect(kill_parent)

	ctransler = zencad.rpc.ApplicationNode(*tpl)
	mw = MainWindow()
	mw.add_view_by_id(winid, ctransler, pid)
	mw.show()
	os.write(w_sync, "sync".encode("utf-8"))
	os.close(w_sync)

	app.exec()


def start_unbound(scn):
	pid = os.getpid()
	r_id, w_id = os.pipe()
	r_sync, w_sync = os.pipe()

	cr1, cw1 = os.pipe()
	cr2, cw2 = os.pipe()

	ctransler = zencad.rpc.EvaluatorNode(cr1, cw2)

	appproc = multiprocessing.Process(target = application_starter, args=(pid, r_id, w_sync, (cr2, cw1)))
	appproc.start()

	app = QApplication([])
	zencad.opengl.init_opengl()
	disp = GeometryWidget(scn)
	os.write(w_id, str(int(disp.winId())).encode("utf-8"))
	os.close(w_id)
	os.read(r_sync, 512)
	os.close(r_sync)

	ctransler.screenCommandSignal.connect(disp.doscreen)

	disp.show()
	app.exec()
