#!/usr/bin/env python3

from zencad import *
import zencad.assemble

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import zencad.libs.kinematic
import zencad.libs.malgo

import time
import termin
import termin.kinchain

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

r.location_update()

r.set_coord(deg(80))
a.rotator.set_coord(deg(50))
b.rotator.set_coord(deg(60))
c.rotator.set_coord(deg(-60))
d.rotator.set_coord(deg(45))


zencad.assemble.unit.print_tree(r)
termin.transform.inspect_tree(r.transform, name_only=True)

bb= b

r.location_update()

chain2 = zencad.libs.kinematic.kinematic_chain(f.output)
chain = termin.kinchain.KinematicChain3(f.output.transform)
disp(a)


stime = time.time()
lasttime = stime
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

    global stime
    stime = time.time()
    global lasttime
    lasttime = stime


tgtshp = sphere(5)
ctr = disp(tgtshp)

K = 1

line = zencad.interactive.line(point3(0,0,0), point3(30,0,30))
#line2 = zencad.interactive.line(point3(0,0,0), point3(30,0,30), color=zencad.color.red)
disp(line)
#disp(line2)

inited = False
def animate(wdg):
    global inited
    global lasttime
    global stime
    if not inited:
        inited = True
        stime = time.time()
        lasttime = stime
        return

    r.location_update()

    curtime = time.time()
    DELTA = curtime - lasttime
    lasttime = curtime

    target_location = translate(
        XSLD.value()/5000*120, YSLD.value()/5000*120, ZSLD.value()/5000*120)

    sens_jacobian = chain.translation_sensitivity_jacobian(
        basis=z.transform.global_pose())
    sens_jacobian2 = chain2.translation_sensivity_jacobian(
        basis=z)

    sens = chain.sensitivity_twists(
        basis=z.transform.global_pose())
    sens2 = chain2.sensivity(
        basis=z)

    
    sens_jacobian_C = c

    error = target_location.translation() - chain.distal.global_pose().lin  

    line.set_points(
        chain.distal.global_pose().lin,
        target_location.translation()
    )
	
    coord0 = chain[0].coord()
    coord1 = chain[1].coord()
    coord2 = chain[2].coord()
    coord3 = chain[3].coord()
    coord4 = chain[4].coord()

    J0 = sens_jacobian
    J2 = chain.translation_sensitivity_jacobian(
        body=c.transform, local=termin.pose3.Pose3.up(60), basis=z.transform.global_pose())
    J1 = chain.translation_sensitivity_jacobian(
        body=d.transform, local=termin.pose3.Pose3.up(60), 
basis=z.transform.global_pose())

    def barrier(x, l):
        if x > l:
            return 0
        else:
            return 1/x+x/(l*l)-2/l

    def biside_barrier(x, l):
        if x > l or x < -l:
            return 0
        else:
            if x >= 0:
                return 1/x+x/(l*l)-2/l
            else:
                return 1/x+x/(l*l)-2/l

    def signsqr(x):
        if x >= 0:
            return x*x
        else:
            return -x*x

    RL = deg(20)
    def Lbi_barrier(c):
        dist_to_180 = (deg(180) - c)
        dist_to_0 = ((deg(0) - c))
        dist_to_m180 = ((deg(-180) - c))
        bar1 = biside_barrier(dist_to_0, RL)
        bar2 = biside_barrier(dist_to_180, RL)
        bar3 = biside_barrier(dist_to_m180, RL)
        return -(bar1 + bar2 + bar3)

    def LL_barrier(c):
        dist_to_180 = (deg(180) - c)
        dist_to_m180 = ((deg(-180) - c))
        bar2 = biside_barrier(dist_to_180, RL)
        bar3 = biside_barrier(dist_to_m180, RL)
        return -(bar2 + bar3)


    def Lbi_tgt(c):
        if c >= 0:
            return (deg(90) - c)**7
        else:
            return (deg(-90) - c)**7

    def LL_tgt(c):
        return (deg(0) - c)**7

    N0 = zencad.libs.malgo.nullspace(sens_jacobian)
    
    I = numpy.diag([1,1,1,1,1])
    barrierM = I
    barrierA = barrierM.dot(barrierM)
    barrierb = barrierM.dot(barrierM).dot(numpy.array([Lbi_barrier(coord0), Lbi_barrier(coord1), Lbi_barrier(coord2), LL_barrier(coord3), 0]))

    wA = N0.T.dot(N0)
    wb = N0.T.dot(N0).dot(numpy.array([Lbi_tgt(coord0), Lbi_tgt(coord1), Lbi_tgt(coord2), LL_tgt(coord3), 0]))

    # N02 = numpy.diag([1,1,1,1,1])
    # kTw2 = 0
    # wA2 = N02.T.dot(N02) * kTw2
    # wb2 = N02.T.dot(N02).dot(numpy.array([L2(coord0), L(coord1), L(coord2), L(coord3), LL(coord4)])) * kTw2
    
    #wA = numpy.diag([1,1,1,1,1])
    #wb = numpy.array([L(coord0), L(coord1), L(coord2), L(coord3), 0])

    kT = 1
    R = 60 * math.sqrt(2)

    E25_1 = d.global_location.translation()
    E25_1[2] = 0
    E25_2 = d.global_location.translation()
    E25_2[0] = 0
    E25_2[1] = 0
    U25_abs_1 = E25_1.length()
    U25_abs_2 = E25_2.length()
    U25_barrier_1 = barrier(U25_abs_1, R)
    U25_barrier_2 = barrier(U25_abs_2, R)
    U25_1 = E25_1 * U25_barrier_1 * 1000
    U25_2 = E25_2 * U25_barrier_2 * 1000
    U25 = U25_1 + U25_2
    N0J2 = J2.dot(N0)
    sA = (N0J2).T.dot(N0J2) * kT
    sb = (N0J2).T.dot(U25) * kT

    E15 = c.global_location.translation()
    E15[2] = 0
    U15_abs = E15.length()
    U15_barrier = barrier(U15_abs, R)
    U15 = E15 * U15_barrier * 1000
    N0J1 = J1.dot(N0)
    sA += (N0J1).T.dot(N0J1) * kT
    sb += (N0J1).T.dot(U15) * kT

    E03 = (chain.distal.global_pose().lin -
        c.global_location.translation())
    U03_abs = E03.length()
    U03_barrier = barrier(U03_abs, R)
    U03 = E03 * U03_barrier * 1000
    N0J0 = J0.dot(N0)
    sA += (N0J0).T.dot(N0J0) * kT
    sb += (N0J0).T.dot(U03) * kT

    E13 = (f.global_location.translation() -
        c.global_location.translation())
    U13_abs = E13.length()
    U13_barrier = barrier(U13_abs, R)
    U13 = E13 * U13_barrier * 1000
    N0J1 = J1.dot(N0)
    sA += (N0J1).T.dot(N0J1) * kT
    sb += (N0J1).T.dot(U13) * kT
    
    m = 1
    kA_h = numpy.diag([m**7,m**7,m**3,m**2,m**1]).dot(N0) * 0.5
    kA = kA_h.T.dot(kA_h)

    A = J0.T.dot(J0) + wA*10000 + barrierA*1000 + sA*0 + kA
    #A = wA
    U = error * K
    b = J0.T.dot(U) + wb*10000 + barrierb*1000 + sb*0
    #print(wb)
    #print(barrierb)
    #print(sb)
    #b = wb

    x = zencad.libs.malgo.svd_solve(A, b)

    #v0 = (J0.dot(x) - U).length()
    #v1 = ((N0J2).dot(x) - U25).length()
    #v2 = ((N0J1).dot(x) - U15).length()
    #v3 = ((N0J0).dot(x) - U03).length()
    #v4 = ((N0J1).dot(x) - U13).length()
    #v5 = numpy.linalg.norm(N0.T.dot(x) - numpy.array([L(coord0), L2(coord1), L(coord2), L(coord3), 0]))
    #sum_v = (v0 + 
    #v1*kT + v2*kT + v3*kT + v4*kT + 
    #v5*kTw)


    coord0 = rad2deg(coord0)
    coord1 = rad2deg(coord1)
    coord2 = rad2deg(coord2)
    coord3 = rad2deg(coord3)

    #print(f"v0:{v0:.2f} v1:{v1:.2f} v2:{v2:.2f} v3:{v3:.2f} v4:{v4:.2f} v5:{v5:.2f} sum:{sum_v:.2f}")
    #print(f"coord: {coord0:.1f} {coord1:.1f} {coord2:.1f} {coord3:.1f}")

    maxsignal = 5
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
	
    chain.apply_coordinate_changes(x * DELTA)
	
    r.update_location_from_transform()

    ctr.relocate(target_location)
    a.location_update()


def close_handle():
    CTRWIDGET.close()


show(animate=animate, preanimate=preanimate, close_handle=close_handle)
