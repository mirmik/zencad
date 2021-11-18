from zencad.gui.display import DisplayWidget
from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL
from zenframe.util import print_to_stderr
import zencad.assemble


class InteractiveControl(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, name, interactive):
        super().__init__(parent)
        self.name = name
        self.interactive = interactive
        self.setText(0, name)
        self.setExpanded(True)

        self.checkbox = QtWidgets.QCheckBox()
        self.transparent = QtWidgets.QLineEdit()
        self.transparent.setText("0.0")
        self.treeWidget().setItemWidget(self, 1, self.transparent)
        self.treeWidget().setItemWidget(self, 2, self.checkbox)

        self.checkbox.clicked.connect(self.hide_or_show)
        self.transparent.textChanged.connect(self.transparent_changed)

    def hide_or_show(self, state):
        deep = not self.isExpanded()
        if self.checkbox.checkState() == QtCore.Qt.Checked:
            self.interactive.hide(True, redraw=True, deep=deep)
        elif self.checkbox.checkState() == QtCore.Qt.Unchecked:
            self.interactive.hide(False, redraw=True, deep=deep)

    def transparent_changed(self):
        deep = not self.isExpanded()
        self.interactive.set_transparency(
            float(self.transparent.text()), redraw=True, deep=deep)


class ViewZone(QtWidgets.QWidget):
    def __init__(self, communicator):
        QtWidgets.QWidget.__init__(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.splitter = QtWidgets.QSplitter()
        self.display = DisplayWidget(communicator)

        self.other_widget = QtWidgets.QTreeWidget()
        HEADERS = ("Имя", "Прозрачность", "Скрыть")
        self.other_widget.setColumnCount(len(HEADERS))
        self.other_widget.setHeaderLabels(HEADERS)

        self.layout.addWidget(self.splitter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.other_widget)
        self.splitter.addWidget(self.display)

        self.setLayout(self.layout)
        self.other_widget.currentItemChanged.connect(self.itemClickedHandle)

    def itemClickedHandle(self, current, previous):
        if previous:
            previous.interactive.highlight(False, redraw=True, deep=True)

        current.interactive.highlight(
            True, redraw=True, deep=not current.isExpanded())

    def attach_scene(self, scene):
        def recurse(item, root):
            if isinstance(item, zencad.assemble.unit):
                if len(item.dispobjects) > 0:
                    root = InteractiveControl(root, item.name(), item)

                for child in item.childs:
                    recurse(child, root)

            else:
                InteractiveControl(root, item.name(), item)

        for item in scene.interactive_roots:
            recurse(item, self.other_widget)

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
