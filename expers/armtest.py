#!/usr/bin/env python3

from zencad import *
import zencad.assemble

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import zencad.libs.kinematic
import zencad.libs.malgo

import time

CTRWIDGET = None
SLDS = None

XSLD = None
YSLD = None
ZSLD = None


class Slider(QSlider):
    def __init__(self):
        super().__init__(Qt.Horizontal)
        self.setRange(-5000, 5000)
        self.setValue(0)
        self.setSingleStep(1)


class link(zencad.assemble.unit):
    def __init__(self, h=60, axis=(0, 1, 0)):
        super().__init__()
        self.add(cylinder(5, h) + cylinder(6, 10,
                center=True).transform(up(h) * short_rotate((0, 0, 1), axis)))
        self.rotator = zencad.assemble.rotator(
            parent=self, axis=axis, location=up(h))

class flink(zencad.assemble.unit):
    def __init__(self, h=60):
        super().__init__()
        self.add(cylinder(5, h))
        self.output = zencad.assemble.unit(
            parent=self, location=up(h))


z = zencad.assemble.unit()
r = zencad.assemble.rotator(axis=(0, 0, 1))
a = link(axis=(0, 1, 0))
b = link(axis=(0, 1, 0))
c = link(axis=(1, 0, 0))
d = link(axis=(1, 0, 0))
f = flink()

r.link(a)
a.rotator.link(b)
b.rotator.link(c)
c.rotator.link(d)
d.rotator.link(f)

r.set_coord(deg(40))
a.rotator.set_coord(deg(50))
b.rotator.set_coord(deg(60))
c.rotator.set_coord(deg(60))
d.rotator.set_coord(deg(60))

bb= b

chain = zencad.libs.kinematic.kinematic_chain(f.output)
disp(a)


def preanimate(widget, animate_thread):
    global CTRWIDGET, XSLD, YSLD, ZSLD
    CTRWIDGET = QWidget()
    layout = QVBoxLayout()
    XSLD = Slider()
    YSLD = Slider()
    ZSLD = Slider()

    XSLD.setValue(2500)
    YSLD.setValue(2500)

    layout.addWidget(XSLD)
    layout.addWidget(YSLD)
    layout.addWidget(ZSLD)

    CTRWIDGET.setLayout(layout)
    CTRWIDGET.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
    CTRWIDGET.show()


tgtshp = sphere(5)
ctr = disp(tgtshp)

K = 1
stime = time.time()
lasttime = stime

line = zencad.interactive.line(point3(0,0,0), point3(30,0,30))
#line2 = zencad.interactive.line(point3(0,0,0), point3(30,0,30), color=zencad.color.red)
disp(line)
#disp(line2)
def animate(wdg):
    global lasttime
    curtime = time.time()
    DELTA = curtime - lasttime
    lasttime = curtime

    target_location = translate(
        XSLD.value()/5000*120, YSLD.value()/5000*120, ZSLD.value()/5000*120)

    sens_jacobian = chain.translation_sensivity_jacobian(
        basis=z)
    
    sens_jacobian_C = c

    error = target_location.translation() - chain.distant.global_location.translation()  

    line.set_points(
        chain.distant.global_location.translation(),
        target_location.translation()
    )
	
    coord0 = chain[0].coord
    coord1 = chain[1].coord
    coord2 = chain[2].coord
    coord3 = chain[3].coord

    J0 = sens_jacobian
    J2 = chain.translation_sensitivity_jacobian2(
        body=c, local=up(60), basis=z)
    J1 = chain.translation_sensitivity_jacobian2(
        body=d, local=up(60), basis=z)

    def barrier(x, l):
        if x > l:
            return 0
        else:
            return 1/x+x/(l*l)-2/l

    def L(c):
        dist_to_0 = c
        dist_to_180 = deg(180) - c
        bar1 = barrier(dist_to_0, deg(90))
        bar2 = -barrier(dist_to_180, deg(90))
        tgt = (deg(90) - c) 
        return (bar1 + bar2)*1000 #+ tgt*20000

    N0 = zencad.libs.malgo.nullspace(sens_jacobian)
    #N0 = numpy.diag([1,1,1,1,1])
    wA = N0.T.dot(N0)
    wb = N0.T.dot(N0).dot(numpy.array([L(coord0), L(coord1), L(coord2), L(coord3), 0]))
    #wA = numpy.diag([1,1,1,1,1])
    #wb = numpy.array([L(coord0), L(coord1), L(coord2), L(coord3), 0])

    E25 = d.global_location.translation()
    E25[2] = 0
    U25_abs = E25.length()
    U25_barrier = barrier(U25_abs, 40)
    U25 = E25 * U25_barrier * 1000
    N0J2 = J2.dot(N0)
    sA = (N0J2).T.dot(N0J2)
    sb = (N0J2).T.dot(U25)
    print(sb)

    E15 = c.global_location.translation()
    E15[2] = 0
    U15_abs = E15.length()
    U15_barrier = barrier(U15_abs, 40)
    U15 = E15 * U15_barrier * 1000
    N0J1 = J1.dot(N0)
    sA += (N0J1).T.dot(N0J1)
    sb += (N0J1).T.dot(U15)

    E03 = (chain.distant.global_location.translation() -
        c.global_location.translation())
    U03_abs = E03.length()
    U03_barrier = barrier(U03_abs, 30)
    U03 = E03 * U03_barrier * 1000
    N0J0 = J0.dot(N0)
    sA += (N0J0).T.dot(N0J0)
    sb += (N0J0).T.dot(U03)

    E13 = (f.global_location.translation() -
        c.global_location.translation())
    U13_abs = E13.length()
    U13_barrier = barrier(U13_abs, 30)
    U13 = E13 * U13_barrier * 1000
    N0J1 = J1.dot(N0)
    sA += (N0J1).T.dot(N0J1)
    sb += (N0J1).T.dot(U13)


    A = J0.T.dot(J0) + wA + sA
    #A = wA
    U = error * K
    b = J0.T.dot(U) + wb + sb
    #b = wb
    x = zencad.libs.malgo.svd_solve(A, b)

    maxsignal = 10
    for i in range(len(x)):
        if x[i] > maxsignal:
            x[i] = maxsignal
        if x[i] < -maxsignal:
            x[i] = -maxsignal
        

    # line2.set_points(
    #     chain.distant.global_location.translation(),
    #     (chain.distant.global_location.translation() + 
    #         J0.dot(x) * 50)
    # )
	
    chain.apply_step(x * DELTA)

    ctr.relocate(target_location)
    a.location_update()


def close_handle():
    CTRWIDGET.close()


show(animate=animate, preanimate=preanimate, close_handle=close_handle)
