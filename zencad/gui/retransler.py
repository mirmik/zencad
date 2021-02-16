import os
import io
import sys

from PyQt5.QtCore import QThread
from zencad.util import print_to_stderr

ENABLE_PREVENT_MODE = True
PREVENT_OUTPUT_START = ' ###### 3D rendering pipe initialisation #####\n'
PREVENT_OUTPUT_STOP = ' ########################################\n'


class ConsoleRetransler(QThread):
    """Ретранслятор перехватывает поток вывода на файловый дескриптор 
    принадлежащий @stdout и читает данные из него в отдельном потоке, 
    перенаправляя их на дескриптор @new_desc.

    Это позволяет перехватывать стандартный вывод в подчинённых процессах и перенаправлять его на встроенную консоль.
    """

    def __init__(self, stdout, new_desc=None):
        super().__init__()
        self.communicator = None
        self.do_retrans(old_file=stdout, new_desc=new_desc)
        self.stop_token = False
        self.prevent_mode = False

    def set_communicator(self, comm):
        self.communicator = comm

    def run(self):
        try:
            self.pid = os.getpid()
            self.readFile = self.r_file
        except Exception as ex:
            sys.stderr.write(
                "console_retransler::rdopen error: ", ex, self.ipipe)
            sys.stderr.write("\r\n")
            sys.stderr.flush()
            exit(0)

        while(True):
            if self.stop_token:
                return
            try:
                inputdata = self.readFile.readline()

                # pythonocc спамит некоторое количество сообщений
                # при активации виджета
                # Этот костыль их скрывает.
                if ENABLE_PREVENT_MODE:
                    if inputdata == PREVENT_OUTPUT_START:
                        self.prevent_mode = True

                    if self.prevent_mode:
                        if inputdata == PREVENT_OUTPUT_STOP:
                            self.prevent_mode = False

                        continue

            except:
                return

            if not self.communicator:
                raise Exception("Communicator not setted")

            self.communicator.send({"cmd": "console", "data": inputdata})

    def finish(self):
        self.stop_token = True

    def do_retrans(self, old_file, new_desc=None):
        old_desc = old_file.fileno()
        if new_desc:
            os.dup2(old_desc, new_desc)
        else:
            new_desc = os.dup(old_desc)

        r, w = os.pipe()
        self.r_file = os.fdopen(r, "r")
        self.w_file = os.fdopen(w, "w")
        self.old_desc = old_desc
        self.new_desc = new_desc
        self.new_file = os.fdopen(new_desc, "w")
        old_file.close()
        os.close(old_desc)
        os.dup2(w, old_desc)

        sys.stdout = io.TextIOWrapper(
            os.fdopen(old_desc, "wb"), line_buffering=True)
