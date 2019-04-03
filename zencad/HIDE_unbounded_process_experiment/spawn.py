import multiprocessing
import zencad.rpc
import runpy
import os
import signal

import zencad.lazifier


def selfkill(pid):
    print("kill")
    signal.kill(pid)


def child_starter(path, ctrlfds):
    import PyQt5
    import PyQt5.QtWidgets

    print("child_starter", ctrlfds)

    # app = PyQt5.QtWidgets.QApplication([])

    # print("make transler")
    ctransler = zencad.rpc.NoQtTransler(*ctrlfds)
    # print("make transler...ok")

    pid = os.getpid()

    def stopworld():
        ctransler.stop()
        selfkill(pid)

    ctransler.callbacks["stopworld"] = stopworld

    # cvar = threading.Event()
    # def runthread(error_store):
    # 	try:
    # 		print("runthread")
    # 		zencad.lazifier.restore_default_lazyopts()
    # 		runpy.run_path(path, run_name="__main__")
    # 		print("subprocess: finished correctly")
    # 		cvar.set()
    # 	except Exception as e:
    # 		error_store.error = e
    # 		print("subprocess: exception raised in executable script: \ntype:{} \ntext:{}".format(e.__class__.__name__, e))
    # 		cvar.set()
    #
    # threading.Thread(target = runthread, args=(error_store,)).start()
    # cvar.wait()
    while 1:
        pass
    print("finish child")


def spawn_clean_process(args, spawner):
    spawner.send("spawn", args=(args))


def spawn_child_process(path, spawner):
    print("spawn child")
    ctrl_r1, ctrl_w1 = os.pipe()
    ctrl_r2, ctrl_w2 = os.pipe()
    multiprocessing.Process(
        target=child_starter, args=(path, (ctrl_r2, ctrl_w1))
    ).start()

    # spawn_clean_process(args=(path, (ctrl_r2,ctrl_w1)), spawner=spawner)
    ctransler = zencad.rpc.ApplicationNode(ctrl_r1, ctrl_w2)

    return ctransler


def clean_spawner(cr1, cw2):
    import pickle

    while 1:
        data = os.read(cr1, 512)
        dct = pickle.loads(data)
        print("clean_spawner receive", dct)
        if dct["cmd"] == "stopworld":
            break
        elif dct["cmd"] == "spawn":
            multiprocessing.Process(target=child_starter, args=dct["args"]).start()


def make_clean_spawner(cr1, cw2):
    pass
    # multiprocessing.Process(target = clean_spawner, args=(cr1,cw2)).start()
