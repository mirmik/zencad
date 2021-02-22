import sys
import subprocess

from zencad.frame.retransler import ConsoleRetransler
from zencad.frame.communicator import Communicator
from zencad.frame.client import Client


def spawn_test_worker(path="", programm="zenframe", sleeped=False, need_prescale=False, size=(640,480)):
    prescale = "--prescale" if need_prescale else ""
    sleeped = "--sleeped" if sleeped else ""
    sizestr = "--size {},{}".format(size[0], size[1]) if size is not None else ""
    interpreter = sys.executable

    if programm == "zenframe":
        programm = "zencad --zenframe"

    cmd = f'{interpreter} -m {programm} "{path}" --unbound {prescale} {sleeped} {sizestr}'

    try:
        subproc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                   close_fds=True)
        return subproc
    except OSError as ex:
        print("Warn: subprocess.Popen finished with exception", ex)
        raise ex

    stdout = io.TextIOWrapper(subproc.stdout, line_buffering=True)
    stdin = io.TextIOWrapper(subproc.stdin, line_buffering=True)

    communicator = Communicator(ifile=stdout, ofile=stdin)
    client = Client(communicator=communicator, subprocess=subproc)

    return client