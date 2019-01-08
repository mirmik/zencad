import multiprocessing
import zencad.rpc
import runpy
import os

import zencad.lazifier

def child_starter(path, ctrlfds):
	print("child_starter")
	def stopworld():
		print("stopworld")

	#app = PyQt5.QtWidgets.QApplication()

	#ctransler = zencad.rpc.EvaluatorNode(*ctrlfds)
	#ctransler.stopworldSignal.connect(stopworld)
#
	#cvar = threading.Event()
	#def runthread(error_store):
	#	try:
	#		print("runthread")
	#		zencad.lazifier.restore_default_lazyopts()
	#		runpy.run_path(path, run_name="__main__")
	#		print("subprocess: finished correctly")
	#		cvar.set()
	#	except Exception as e:
	#		error_store.error = e
	#		print("subprocess: exception raised in executable script: \ntype:{} \ntext:{}".format(e.__class__.__name__, e))
	#		cvar.set()
#
	#threading.Thread(target = runthread, args=(error_store,)).start()
	#cvar.wait()
	print("finish child")

def spawn_clean_process(target, args, spawner):
	spawner.send("spawn", args=(target,args))

def spawn_child_process(path, spawner):
	print("spawn child")
	ctrl_r1, ctrl_w1 = os.pipe()
	ctrl_r2, ctrl_w2 = os.pipe()

	#multiprocessing.Process(target = child_starter, args=(path, (ctrl_r2,ctrl_w1)))
	spawn_clean_process(target = child_starter, args=(path, (ctrl_r2,ctrl_w1)), spawner=spawner)
	ctransler = zencad.rpc.ApplicationNode(ctrl_r1, ctrl_w2)

	return ctransler

def clean_spawner(cr1, cw2):
	import pickle
	while 1:
		data = os.read(cr1, 512)
		print("clean_spawner::read", pickle.loads(data))

def make_clean_spawner(cr1, cw2):
	multiprocessing.Process(target = clean_spawner, args=(cr1,cw2)).start()