#!/usr/bin/env python3

import time
import math
import random

from zencad import *
import zencad.assemble

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

CTRWIDGET = None
SLD0 = None
SLD1 = None

BALL_POSITION = [0, 0]
BALL_SPEED_NORMAL = math.sqrt(150**2 * 2)
BALL_SPEED = [
    BALL_SPEED_NORMAL*math.cos(deg(45)),
    BALL_SPEED_NORMAL*math.cos(deg(45))]

BOX_WIDTH = 300
BOX_LENGTH = 500
PLAYER_OFF = 40
T = 10


class Slider(QSlider):
    def __init__(self):
        super().__init__(Qt.Horizontal)
        self.setRange(-5000, 5000)
        self.setValue(0)
        self.setSingleStep(1)

    _value = QSlider.value

    def value(self):
        return self._value(self) / 10000 * (BOX_WIDTH-80)


class player(zencad.assemble.unit):
    def __init__(self):
        super().__init__()
        self.add(box(80, 10, 10, center=True))


class ball(zencad.assemble.unit):
    def __init__(self):
        super().__init__()
        self.add(sphere(5))


player_one = player()
player_two = player()
ball = ball()

BOX = box(BOX_WIDTH+T*2, BOX_LENGTH+T*2+PLAYER_OFF*2, 20, center=True) - \
    box(BOX_WIDTH, BOX_LENGTH+PLAYER_OFF*2, 20, center=True)

disp(player_one)
disp(player_two)
disp(ball)
disp(BOX)


def change_angle():
    global BALL_SPEED

    angle = math.atan2(BALL_SPEED[1], BALL_SPEED[0])
    angle += random.uniform(-0.2, 0.2)

    BALL_SPEED = [math.cos(angle) * BALL_SPEED_NORMAL,
                  math.sin(angle) * BALL_SPEED_NORMAL]


def preanimate(wdg, animate_thread):
    global CTRWIDGET, SLD0, SLD1
    CTRWIDGET = QWidget()
    layout = QVBoxLayout()

    SLD0 = Slider()
    SLD1 = Slider()

    layout.addWidget(SLD1)
    layout.addWidget(SLD0)

    CTRWIDGET.setLayout(layout)
    CTRWIDGET.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
    CTRWIDGET.show()


stime = time.time()
lasttime = stime


def animate(wdg):
    global BALL_POSITION
    global lasttime
    curtime = time.time()
    DELTA = curtime - lasttime
    lasttime = curtime

    player_one_pos = SLD0.value()
    player_one_location = translate(SLD0.value(), -BOX_LENGTH/2-5, 0)
    player_one.relocate(player_one_location, view=True)

    player_two_pos = SLD1.value()
    player_two_location = translate(SLD1.value(), BOX_LENGTH/2+5, 0)
    player_two.relocate(player_two_location, view=True)

    BALL_POSITION[0] += BALL_SPEED[0] * DELTA
    BALL_POSITION[1] += BALL_SPEED[1] * DELTA

    if BALL_POSITION[0] > BOX_WIDTH/2:
        BALL_SPEED[0] = - BALL_SPEED[0]
        BALL_POSITION[0] = BOX_WIDTH/2
        change_angle()

    if BALL_POSITION[0] < -BOX_WIDTH/2:
        BALL_SPEED[0] = - BALL_SPEED[0]
        BALL_POSITION[0] = -BOX_WIDTH/2
        change_angle()

    if BALL_POSITION[1] > BOX_LENGTH/2:
        BALL_SPEED[1] = - BALL_SPEED[1]
        BALL_POSITION[1] = BOX_LENGTH/2
        if abs(player_two_pos - BALL_POSITION[0]) > 40:
            BALL_POSITION = [0, 0]
        change_angle()

    if BALL_POSITION[1] < -BOX_LENGTH/2:
        BALL_SPEED[1] = - BALL_SPEED[1]
        BALL_POSITION[1] = -BOX_LENGTH/2
        if abs(player_one_pos - BALL_POSITION[0]) > 40:
            BALL_POSITION = [0, 0]
        change_angle()

    ball.relocate(translate(BALL_POSITION[0], BALL_POSITION[1]), view=True)


def close_handle():
    CTRWIDGET.close()


show(animate=animate, preanimate=preanimate, close_handle=close_handle)
