from zencad.frame.util import print_to_stderr

class Client:
    """ Хранит объекты, связанные с управлением одним клиентом. """

    def __init__(self, communicator=None, subprocess=None):
        self.communicator = communicator
        self.subprocess = subprocess
        self.embeded_window = None
        self.embeded_widget = None

    def set_embed(self, window, widget):
        self.embeded_window = window
        self.embeded_widget = widget

    def pid(self):
        if self.subprocess:
            return self.subprocess.pid
        else:
            return self.communicator.declared_opposite_pid

    def send(self, *args, **kwargs):
        return self.communicator.send(*args, **kwargs)

    def terminate(self):
        self.communicator.stop_listen()
        self.subprocess.terminate()
