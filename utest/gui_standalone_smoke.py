#!/usr/bin/env python3
"""Exercise direct show() in one process without foreign window embedding."""


def main():
    from zencad.gui.qt_backend import configure_qt_platform

    configure_qt_platform()

    from PyQt5 import QtCore, QtWidgets
    from zencad import box, display, show, translate

    controller = display(box(10, center=True))
    state = {"updates": 0, "closed": False, "window": None}

    def animate(animation_state):
        state["updates"] += 1
        controller.relocate(translate(state["updates"], 0, 0))

    def preanimate(widget, animation_thread):
        application = QtWidgets.QApplication.instance()
        assert application is not None
        assert widget.parent() is None
        state["window"] = int(widget.winId())
        QtCore.QTimer.singleShot(500, widget.close)

    def close_handle():
        state["closed"] = True
        assert state["updates"] > 0
        print("ZenCad same-process standalone smoke: OK")

    show(
        animate=animate,
        preanimate=preanimate,
        close_handle=close_handle,
        animate_step=0.01,
    )


if __name__ == "__main__":
    main()
