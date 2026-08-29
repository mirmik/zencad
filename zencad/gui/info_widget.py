from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import math

QMARKER_MESSAGE = "Press 'F3' to set marker"
WMARKER_MESSAGE = "Press 'F4' to set marker"
MEASUREMENT_DEFAULT_MESSAGE = "Marker difference and distance"


class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.infolay = QHBoxLayout()

        self.poslbl = QLabel("Tracking disabled")
        self.poslbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.poslbl.setAlignment(Qt.AlignCenter)

        self.marker1Label = QLabel(QMARKER_MESSAGE)
        self.marker1Label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.marker1Label.setStyleSheet(
            "QLabel { background-color : rgb(100,0,0); color : white; }"
        )
        self.marker1Label.setAlignment(Qt.AlignCenter)

        self.marker2Label = QLabel(WMARKER_MESSAGE)
        self.marker2Label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.marker2Label.setStyleSheet(
            "QLabel { background-color : rgb(0,100,0); color : white; }"
        )
        self.marker2Label.setAlignment(Qt.AlignCenter)

        self.markerDistLabel = QLabel(MEASUREMENT_DEFAULT_MESSAGE)
        self.markerDistLabel.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.markerDistLabel.setAlignment(Qt.AlignCenter)

        self.infolay.addWidget(self.poslbl)
        self.infolay.addWidget(self.marker1Label)
        self.infolay.addWidget(self.marker2Label)
        self.infolay.addWidget(self.markerDistLabel)
        self.infolay.setStretch(0, 3)
        self.infolay.setStretch(1, 3)
        self.infolay.setStretch(2, 3)
        self.infolay.setStretch(3, 5)

        self.infolay.setContentsMargins(0, 0, 0, 0)
        self.infolay.setSpacing(0)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setLayout(self.infolay)

        self.saved_data = {"q": None, "w": None}

    def set_marker_data(self, qw, x, y, z):
        data = "x:{:8.3f},  y:{:8.3f},  z:{:8.3f}".format(x, y, z)
        label = self.marker1Label if qw == "q" else self.marker2Label

        if (x, y, z) == (0, 0, 0):
            label.setText(QMARKER_MESSAGE if qw == "q" else WMARKER_MESSAGE)
            self.saved_data[qw] = None

        else:
            label.setText(data)
            self.saved_data[qw] = (x, y, z)

        self.update_dist()

    def update_dist(self):
        if self.saved_data["q"] is None or self.saved_data["w"] is None:
            self.markerDistLabel.setText(MEASUREMENT_DEFAULT_MESSAGE)
            return

        qx, qy, qz = self.saved_data["q"]
        wx, wy, wz = self.saved_data["w"]

        dx, dy, dz = qx - wx, qy - wy, qz - wz
        dist = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        self.markerDistLabel.setText(
            "Δ(F3−F4): ({:.3f}, {:.3f}, {:.3f})   Distance: {:.3f}".format(
                dx, dy, dz, dist
            )
        )

    def set_tracking_info(self, data):
        ok = data[1]
        data = data[0]

        if ok:
            self.poslbl.setText("x:{:8.3f} y:{:8.3f} z:{:8.3f}".format(*data))
        else:
            self.poslbl.setText("")

    def set_tracking_info_status(self, en):
        if en:
            self.poslbl.setText("")
        else:
            self.poslbl.setText("Tracking disabled")
