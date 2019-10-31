import signal
import psutil
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Call this function in your main after creating the QApplication
def setup_qt_interrupt_handling():
    """Setup handling of KeyboardInterrupt (Ctrl-C) for PyQt."""
    signal.signal(signal.SIGINT, _qt_interrupt_handler)
    # Regularly run some (any) python code, so the signal handler gets a
    # chance to be executed:
    safe_timer(50, lambda: None)

def setup_simple_interrupt_handling():
    signal.signal(signal.SIGINT, _simple_interrupt_handler)


# Define this as a global function to make sure it is not garbage
# collected when going out of scope:
def _qt_interrupt_handler(signum, frame):
    """Handle KeyboardInterrupt: quit application."""
    procs = psutil.Process().children() 
    for p in procs:
        p.terminate()

    QApplication.quit()

# Define this as a global function to make sure it is not garbage
# collected when going out of scope:
def _simple_interrupt_handler(signum, frame):
    sys.exit(0)

def safe_timer(timeout, func, *args, **kwargs):
    """
    Create a timer that is safe against garbage collection and overlapping
    calls. See: http://ralsina.me/weblog/posts/BB974.html
    """
    def timer_event():
        try:
            func(*args, **kwargs)
        finally:
            QTimer.singleShot(timeout, timer_event)
    QTimer.singleShot(timeout, timer_event)