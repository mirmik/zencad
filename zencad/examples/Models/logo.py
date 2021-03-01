#!/usr/bin/env python3
# coding: utf-8

import evalcache
from zencad import *

mandarinc = os.path.join(zencad.moduledir, "examples", "fonts/mandarinc.ttf")
fontpath = register_font(mandarinc)

NUT_RENDER = True
DISPLAY_BOLT = False


@lazy
def instrument_metric_nut(drad, step, h):
    H = step * math.tan(deg(60))

    pseg = polysegment(
        points(
            [
                (drad + H / 2, 0, 0),
                (drad - H / 4, 0, -(3 / 8 * step)),
                (drad - H / 4, 0, -(5 / 8 * step)),
                (drad + H / 2, 0, -step),
            ]
        ),
        closed=True,
    )

    path = helix(r=drad, h=h, step=step)
    base = pipe_shell(spine=path, arr=[pseg], frenet=True)
    return base


@lazy
def metric_nut(d, step, h, render=False):
    H = step * math.tan(deg(60))
    drad = d / 2 - 3 / 8 * H
    cil = cylinder(r=d / 2, h=h)
    instr = instrument_metric_nut(drad=drad, step=step, h=h + step)

    if render:
        print("Please wait. It may take a while.")
        return cil - instr
    else:
        return cil


nut = metric_nut(8, 1.25, 50, render=NUT_RENDER)

bolt = (
    nut.up(15.3)
    + cylinder(r=8 / 2, h=10).up(5.3)
    + linear_extrude(ngon(r=7.1, n=6), (0, 0, 5.3))
).rotateY(deg(90))

l = 70.68
w = 13.5
h = 8.5

base = loft([
    rectangle(l, w, center=True, wire=True),
    rectangle(l+5, w+5, center=True, wire=True).down(h)
])
bolt = bolt.left(l/2 - 2.3)

m = textshape("ZenCad", "Mandarinc", 20)
m = m.translate(- m.center())
m = m.extrude(6) + base
m = m - bolt

if DISPLAY_BOLT:
    disp(bolt)

disp(m, color=(0.6, 1, 1, 0.3))
show()
