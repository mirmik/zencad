from zencad.gui.display import DisplayWidget
from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL
from zenframe.util import print_to_stderr


class InteractiveControl(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, name, interactive):
        super().__init__(parent)
        self.name = name
        self.interactive = interactive
        self.setText(0, "fasdasfdaf")

        self.checkbox = QtWidgets.QCheckBox()
        self.treeWidget().setItemWidget(self, 1, QtWidgets.QLabel("fsadfsadf"))
        self.treeWidget().setItemWidget(self, 2, self.checkbox)

        self.checkbox.clicked.connect(self.hide_or_show)

    def hide_or_show(self, state):
        if self.checkbox.checkState() == QtCore.Qt.Checked:
            self.interactive.hide(True, redraw=True)
        elif self.checkbox.checkState() == QtCore.Qt.Unchecked:
            self.interactive.hide(False, redraw=True)


class ViewZone(QtWidgets.QWidget):
    def __init__(self, communicator):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.splitter = QtWidgets.QSplitter()
        self.display = DisplayWidget(communicator)

        self.other_widget = QtWidgets.QTreeWidget()
        HEADERS = ("column 1", "column 3", "column 2")
        self.other_widget.setColumnCount(len(HEADERS))
        self.other_widget.setHeaderLabels(HEADERS)

        self.layout.addWidget(self.splitter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.other_widget)
        self.splitter.addWidget(self.display)

        self.setLayout(self.layout)

    def attach_scene(self, scene):
        for item in scene.interactives:
            InteractiveControl(self.other_widget, str(item), item)
        return self.display.attach_scene(scene)

    def external_communication_command(self, data):
        cmd = data["cmd"]
        try:
            if cmd == "resize":
                self.resize(data["size"][0], data["size"][1])
                self.display._display.View.MustBeResized()
                return

        except Exception as ex:
            print_to_stderr("Error on external command handling", repr(ex))

        return self.display.external_communication_command(data)
