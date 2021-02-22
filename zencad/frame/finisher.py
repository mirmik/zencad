import signal
import psutil
from zencad.frame.util import print_to_stderr

FINISH_HANDLER = None

def finish_procedure():
    procs = psutil.Process().children()
    for p in procs:
        p.terminate()

    for p in procs:
        p.wait()

def setup_finish_handler(handler):
    global FINISH_HANDLER
    FINISH_HANDLER = handler

def interrupt_handler(a, b):
    print_to_stderr(a,b)

    if FINISH_HANDLER:
        FINISH_HANDLER()

    finish_procedure()
    exit()

def setup_interrupt_handlers():
    signal.signal(signal.SIGINT, interrupt_handler)
    signal.signal(signal.SIGTERM, interrupt_handler)