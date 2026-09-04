#!/usr/bin/env python3
"""Managed two-player tennis: arrows control player 1, A/D player 2."""

import math
import random

from zencad import *
import zencad.assemble

BALL_POSITION = [0, 0]
BALL_SPEED_NORMAL = math.sqrt(150**2 * 2)
BALL_SPEED = [
    BALL_SPEED_NORMAL*math.cos(deg(45)),
    BALL_SPEED_NORMAL*math.cos(deg(45))]

BOX_WIDTH = 300
BOX_LENGTH = 500
PLAYER_OFF = 40
T = 10
PLAYER_POSITIONS = [0.0, 0.0]
PLAYER_SPEED = 180.0


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


def animate(state):
    global BALL_POSITION
    delta = min(state.delta, 0.1)
    limit = (BOX_WIDTH - 80) / 2

    PLAYER_POSITIONS[0] += PLAYER_SPEED * delta * (
        state.input.key_down("right") - state.input.key_down("left")
    )
    PLAYER_POSITIONS[1] += PLAYER_SPEED * delta * (
        state.input.key_down("d") - state.input.key_down("a")
    )
    PLAYER_POSITIONS[0] = max(-limit, min(limit, PLAYER_POSITIONS[0]))
    PLAYER_POSITIONS[1] = max(-limit, min(limit, PLAYER_POSITIONS[1]))

    player_one_pos = PLAYER_POSITIONS[0]
    player_one_location = translate(player_one_pos, -BOX_LENGTH/2-5, 0)
    player_one.relocate(player_one_location, view=True)

    player_two_pos = PLAYER_POSITIONS[1]
    player_two_location = translate(player_two_pos, BOX_LENGTH/2+5, 0)
    player_two.relocate(player_two_location, view=True)

    BALL_POSITION[0] += BALL_SPEED[0] * delta
    BALL_POSITION[1] += BALL_SPEED[1] * delta

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


show(animate=animate, animate_step=0.01)
