#!/usr/bin/env python3

from zencad import *
import zencad.assemble

import time
import numpy


class HeadAssemble(zencad.assemble.unit):
    def __init__(self):
        super().__init__()

        self.add(cylinder(r=8, h=5).up(3) + cylinder(r=4, h=3))

        eye0 = self.add(cylinder(r=3, h=3).rotateX(
            deg(90)).left(5).back(8).up(3 + 2.5))
        eye1 = self.add(cylinder(r=3, h=3).rotateX(
            deg(90)).right(5).back(8).up(3 + 2.5))

        eye0.set_color(0.3, 0, 0)
        eye1.set_color(0.3, 0, 0)


class Robot(zencad.assemble.unit):
    h = 20
    r = 10
    aw = 4

    def __init__(self):
        super().__init__()

        arm_model = (
            zencad.box(self.aw, self.aw, self.h / 2, center=True)
            .down(self.h / 4 - self.aw / 2)
            .rotateY(deg(90))
        )
        body_model = zencad.cylinder(r=self.r, h=self.h)
        arm_translate = translate(
            self.r + self.aw / 2, 0, self.h / 6 * 4) * rotateY(-deg(90))

        self.add(body_model)

        self.left_arm_connector = zencad.assemble.spherical_rotator(
            parent=self, location=mirrorYZ() * arm_translate)
        self.right_arm_connector = zencad.assemble.spherical_rotator(
            parent=self, location=arm_translate)

        self.left_arm_connector.output.add(arm_model)
        self.right_arm_connector.output.add(arm_model)

        head = HeadAssemble()

        self.head_connector = zencad.assemble.rotator(
            parent=self, location=up(self.h), axis=(0, 0, 1))
        self.head_connector.link(head)


base = box(100, 100, 1, center=True).down(0.5)
robot0 = Robot()

register_font(os.path.join(zencad.moduledir, "examples/fonts/mandarinc.ttf"))
text = textshape(text="Brutality", fontname="Mandarinc", size=15).extrude(2)
tcenter = text.center()
text = text.translate(-tcenter.x, -tcenter.y, -tcenter.z)
text = text.back(20).up(5)

disp(robot0, deep=True)
disp(base, color=(0.3, 0.3, 0.3))

robot0.location_update(deep=True, view=True)

text_controller = disp(text, color=(0.5, 0, 0))
text_controller.hide(True)
texthided = True

wsq = 30

corner0 = point3(-wsq, -wsq, 0)
corner1 = point3(wsq, -wsq, 0)
corner2 = point3(wsq, wsq, 0)
corner3 = point3(-wsq, wsq, 0)
center = point3(0, 0, 0)
center2 = point3(0, 0, robot0.r)


def domovie(t):
    global texthided

    if 0 < t < 2:
        robot0.relocate(
            translate(*(corner0 + (corner1 - corner0) * ((t - 0) / 2)))
            * rotateZ(deg(90))
        )
    if 2 < t < 4:
        robot0.relocate(translate(*corner1) *
                        rotateZ(deg(90 + 90 * ((t - 2) / 2))))

    if 4 < t < 6:
        robot0.relocate(
            translate(*(corner1 + (corner2 - corner1) * ((t - 4) / 2)))
            * rotateZ(deg(180))
        )
    if 6 < t < 8:
        robot0.relocate(
            translate(*corner2) * rotateZ(deg(180 + 90 * ((t - 6) / 2)))
        )
    if 8 < t < 10:
        robot0.relocate(
            translate(*(corner2 + (corner3 - corner2) * ((t - 8) / 2)))
            * rotateZ(deg(270))
        )
    if 10 < t < 12:
        robot0.relocate(
            translate(*corner3) * rotateZ(deg(270 + 90 * ((t - 10) / 2)))
        )
    if 12 < t < 14:
        robot0.relocate(
            translate(*(corner3 + (corner0 - corner3) * ((t - 12) / 2)))
            * rotateZ(deg(0))
        )
    if 14 < t < 16:
        robot0.relocate(
            translate(*corner0) * rotateZ(deg(0 + 135 * ((t - 14) / 2)))
        )
    if 16 < t < 18:
        robot0.relocate(
            translate(*(corner0 + (center - corner0) * ((t - 16) / 2)))
            * rotateZ(deg(135))
        )
    if 18 < t < 20:
        robot0.relocate(
            translate(*center) * rotateZ(deg(135 + (-135) * ((t - 18) / 2)))
        )

    if 20 < t < 22:
        robot0.left_arm_connector.set_yaw(-deg(-90 +
                                               90 * math.cos((t - 20) * math.pi / 4)))
        robot0.right_arm_connector.set_yaw(-deg(-90 +
                                                90 * math.cos((t - 20) * math.pi / 4)))

    if 22 < t < 24:
        robot0.left_arm_connector.set_yaw(-deg(-90 +
                                               90 * math.sin((t - 22) * math.pi)))
        robot0.right_arm_connector.set_yaw(-deg(-90 -
                                                90 * math.sin((t - 22) * math.pi)))

    if 24 < t < 26:
        robot0.head_connector.set_coord(deg(45 * math.sin((t - 24) * math.pi)))
        robot0.left_arm_connector.set_yaw(-deg(-90 +
                                               90 * math.sin((t - 24) * math.pi)))
        robot0.right_arm_connector.set_yaw(-deg(-90 -
                                                90 * math.sin((t - 24) * math.pi)))

    if 26 < t < 28:
        robot0.relocate(rotateZ(deg(360 * ((t - 26) / 2))))
        robot0.head_connector.set_coord(deg(45 * math.sin((t - 26) * math.pi)))
        robot0.left_arm_connector.set_yaw(-deg(-90 +
                                               90 * math.sin((t - 26) * math.pi)))
        robot0.right_arm_connector.set_yaw(-deg(-90 -
                                                90 * math.sin((t - 26) * math.pi)))

    if 28 < t < 30:
        robot0.relocate(rotateZ(deg(-360 * ((t - 28) / 2))))
        robot0.head_connector.set_coord(deg(45 * math.sin((t - 28) * math.pi)))
        robot0.left_arm_connector.set_yaw(-deg(-90 +
                                               90 * math.sin((t - 28) * math.pi)))
        robot0.right_arm_connector.set_yaw(-deg(-90 -
                                                90 * math.sin((t - 28) * math.pi)))

    if 30 < t < 32:
        robot0.left_arm_connector.set_yaw(-deg(-90 *
                                               math.cos((t - 30) * math.pi / 4)))
        robot0.right_arm_connector.set_yaw(-deg(-90 *
                                                math.cos((t - 30) * math.pi / 4)))

    if 32 < t < 34:
        robot0.left_arm_connector.set_pitch(deg(-90 * (t - 32) / 2))
        robot0.right_arm_connector.set_pitch(deg(-135 * (t - 32) / 2))

    if 34 < t < 36:
        robot0.relocate(
            translate(*((center2 - center) * (t - 34) / 2))
            * rotateX(deg(-90 * (t - 34) / 2))
        )

    if t > 36 and texthided is True:
        text_controller.hide(False)
        texthided = False


start_time = time.time()


def animate(wdg):
    t = time.time() - start_time
    t = t + 0
    domovie(t)
    robot0.location_update(deep=True, view=True)


show(animate=animate)
