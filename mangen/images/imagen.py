#! /usr/bin/env python3
# coding: utf-8

from zencad import *
import os

import zencad.visual
import zencad.internal_models
import zencad.platonic
import pyservoce

# lazy.diag = True

wsize = (300, 200)

dock = lambda sz: box(sz,sz,2,center=True).down(1)

if not os.path.exists("generic"):
    os.makedirs("generic")


@lazy.file_creator(pathfield="path")
def doscreen_impl(model, path, size, yaw=None, pitch=None, triedron=True):
    scn = Scene()
    try:
        mmm = model
        if isinstance(mmm, evalcache.LazyObject):
            mmm = mmm.unlazy()
        scn.add(mmm)
    except:
        for m in model:
            if isinstance(m, (tuple, list)):
                c=m[1]
                m=m[0]
            else:
                c=zencad.default_color

            mod = m
            if isinstance(mod, evalcache.LazyObject):
                mod = mod.unlazy()

            if isinstance(mod, pyservoce.point3):
                scn.add(mod, color(1, 0, 0))

            else:
                scn.add(mod, c)

    viewer = scn.viewer
    if triedron: # Always add triedron 
        viewer.set_triedron_axes()
    view = viewer.create_view()
    view.set_triedron(False)
    view.set_virtual_window(size[0], size[1])

    if yaw is None:
        yaw = math.pi * (7 / 16) + math.pi / 2
    if pitch is None:
        pitch = math.pi * -0.15
    view.set_direction(
        math.cos(pitch) * math.cos(yaw),
        math.cos(pitch) * math.sin(yaw),
        math.sin(pitch),
    )
    view.set_orthogonal()
    view.fit_all()

    zencad.visual.screen_view(view, path, size)


def doscreen(model, path, size, yaw=None, pitch=None, triedron=True):
    print("screen (path:{0}, size:{1}, model:{2})".format(path, size, model))
    doscreen_impl(
        model, "generic/" + path, size, yaw=yaw, pitch=pitch, triedron=triedron
    )


yaw = math.pi * (7 / 16)
pitch = math.pi * -0.20
doscreen(
    model=box(200, 200, 200, center=True)
    - sphere(120)
    + sphere(60).rotateX(deg(90)).rotateZ(deg(90)),
    path="zencad-logo.png",
    size=(500, 400),
    yaw=yaw,
    pitch=pitch,
)

# prim3d
doscreen(model=box(10, 20, 30, center=False), path="box0.png", size=wsize)
doscreen(model=box(10, center=True), path="box1.png", size=wsize)

doscreen(model=sphere(r=10), path="sphere0.png", size=wsize)
doscreen(model=sphere(r=10, yaw=deg(120)), path="sphere1.png", size=wsize)
doscreen(model=sphere(r=10, pitch=(deg(20), deg(60))), path="sphere2.png", size=wsize)
doscreen(
    model=sphere(r=10, yaw=deg(120), pitch=(deg(20), deg(60))),
    path="sphere3.png",
    size=wsize,
)

doscreen(model=cylinder(r=10, h=20), path="cylinder0.png", size=wsize)
doscreen(model=cylinder(r=10, h=20, yaw=deg(45)), path="cylinder1.png", size=wsize)
doscreen(model=cylinder(r=10, h=20, center=True), path="cylinder2.png", size=wsize)
doscreen(model=cylinder(r=10, h=20, yaw=deg(45), center=True), path="cylinder3.png", size=wsize)

doscreen(model=cone(r1=20, r2=10, h=20), path="cone0.png", size=wsize)
doscreen(model=cone(r1=20, r2=10, h=20, yaw=deg(45)), path="cone1.png", size=wsize)
doscreen(model=cone(r1=0, r2=20, h=20), path="cone2.png", size=wsize)
doscreen(model=cone(r1=20, r2=0, h=20, center=True), path="cone3.png", size=wsize)

doscreen(model=torus(r1=20, r2=5), path="torus0.png", size=wsize)
doscreen(model=torus(r1=20, r2=5, yaw=deg(120)), path="torus1.png", size=wsize)
doscreen(
    model=torus(r1=20, r2=5, pitch=(deg(-20), deg(120))), path="torus2.png", size=wsize
)
doscreen(
    model=torus(r1=20, r2=5, pitch=(deg(-20), deg(120)), yaw=deg(120)),
    path="torus3.png",
    size=wsize,
)
doscreen(
    model=torus(r1=20, r2=5, pitch=(deg(-140), deg(140)), yaw=deg(120)),
    path="torus4.png",
    size=wsize,
)
doscreen(
    model=torus(r1=20, r2=5, pitch=(deg(-20), deg(190)), yaw=deg(120)),
    path="torus5.png",
    size=wsize,
)

doscreen(
    model=sphere(r=10) - halfspace().rotateX(deg(150)),
    path="halfspace0.png",
    size=wsize,
)
doscreen(
    model=sphere(r=10) ^ halfspace().rotateX(deg(150)),
    path="halfspace1.png",
    size=wsize,
)

# prim2d
yaw2d = math.pi / 2 + math.pi * 1 / 8
pitch2d = -math.pi * 4 / 16

doscreen(
    model=rectangle(20, 10),
    path="rectangle0.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=rectangle(20, 10, wire=True),
    path="rectangle1.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=rectangle(20),
    path="rectangle2.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=rectangle(20, wire=True),
    path="rectangle3.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)

doscreen(
    model=circle(r=20),
    path="circle0.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=circle(r=20, wire=True),
    path="circle1.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=circle(r=20, angle=(deg(45), deg(90))),
    path="circle2.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=circle(r=20, angle=(deg(45), deg(90)), wire=True),
    path="circle3.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)

doscreen(
    model=ellipse(r1=40, r2=20),
    path="ellipse0.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=ellipse(r1=40, r2=20, wire=True),
    path="ellipse1.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=ellipse(r1=40, r2=20, angle=(deg(45), deg(90))),
    path="ellipse2.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=ellipse(r1=40, r2=20, angle=(deg(45), deg(90)), wire=True),
    path="ellipse3.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)

doscreen(
    model=polygon(pnts=[(0, 0), (0, 40), (20, 10), (10, 0)]),
    path="polygon0.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=polygon(pnts=[(0, 0), (0, 40), (20, 10), (10, 0)], wire=True),
    path="polygon1.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)

doscreen(
    model=ngon(r=20, n=3),
    path="ngon0.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=ngon(r=20, n=3, wire=True),
    path="ngon1.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=ngon(r=20, n=5),
    path="ngon2.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=ngon(r=20, n=5, wire=True),
    path="ngon3.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=ngon(r=20, n=8),
    path="ngon4.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=ngon(r=20, n=8, wire=True),
    path="ngon5.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)

doscreen(
    model=textshape(
        text="TextShape", fontpath="../../zencad/examples/fonts/testfont.ttf", size=100
    ),
    path="textshape0.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)
doscreen(
    model=textshape(
        text="TextShape", fontpath="../../zencad/examples/fonts/mandarinc.ttf", size=100
    ),
    path="textshape1.png",
    size=wsize,
    yaw=yaw2d,
    pitch=pitch2d,
    triedron=True,
)

doscreen(
    model=[segment((10, 10, 10), (20, 10, 10)), point3(10, 10, 10), point3(20, 10, 10)],
    path="segment0.png",
    size=wsize,
)

doscreen(
    model=[
        polysegment([(0, 0, 0), (0, 10, 10), (0, 10, 20), (0, -10, 20), (0, -10, 10)]),
        point3(0, 0, 0),
        point3(0, 10, 10),
        point3(0, 10, 20),
        point3(0, -10, 20),
        point3(0, -10, 10),
    ],
    path="polysegment0.png",
    size=wsize,
)
doscreen(
    model=[
        polysegment(
            [(0, 0, 0), (0, 10, 10), (0, 10, 20), (0, -10, 20), (0, -10, 10)],
            closed=True,
        ),
        point3(0, 0, 0),
        point3(0, 10, 10),
        point3(0, 10, 20),
        point3(0, -10, 20),
        point3(0, -10, 10),
    ],
    path="polysegment1.png",
    size=wsize,
)

doscreen(
    model=[
        circle_arc((0, 0, 0), (0, 10, 10), (0, 10, 20)),
        point3(0, 0, 0),
        point3(0, 10, 10),
        point3(0, 10, 20),
    ],
    path="circle_arc0.png",
    size=wsize,
)

doscreen(model=helix(r=10, h=20, step=1), path="helix0.png", size=wsize)
doscreen(model=helix(r=10, h=20, step=1, left=True), path="helix1.png", size=wsize)
doscreen(model=helix(r=10, h=20, step=1, angle=deg(10)), path="helix2.png", size=wsize)
doscreen(model=helix(r=10, h=20, step=1, angle=-deg(10)), path="helix3.png", size=wsize)


yaw = -math.pi / 4
pitch = -math.pi * 1 / 8

yaw1 = 0
pitch1 = 0

yaw2 = math.pi / 2
pitch2 = 0

yaw3 = 0
pitch3 = -math.pi / 2 + 0.00001

doscreen(
    model=sphere(r=10)
    + cylinder(r=5, h=30, center=True)
    + ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="union.png",
    size=wsize,
    yaw=yaw,
    pitch=pitch,
    triedron=False
)
doscreen(
    model=sphere(r=10)
    + cylinder(r=5, h=30, center=True)
    + ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="union0.png",
    size=wsize,
    yaw=yaw1,
    pitch=pitch1,
)
doscreen(
    model=sphere(r=10)
    + cylinder(r=5, h=30, center=True)
    + ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="union1.png",
    size=wsize,
    yaw=yaw2,
    pitch=pitch2,
)
doscreen(
    model=sphere(r=10)
    + cylinder(r=5, h=30, center=True)
    + ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="union2.png",
    size=wsize,
    yaw=yaw3,
    pitch=pitch3,
)

doscreen(
    model=sphere(r=10)
    - cylinder(r=5, h=30, center=True)
    - ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="difference.png",
    size=wsize,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=sphere(r=10)
    - cylinder(r=5, h=30, center=True)
    - ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="difference0.png",
    size=wsize,
    yaw=yaw1,
    pitch=pitch1,
)
doscreen(
    model=sphere(r=10)
    - cylinder(r=5, h=30, center=True)
    - ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="difference1.png",
    size=wsize,
    yaw=yaw2,
    pitch=pitch2,
)
doscreen(
    model=sphere(r=10)
    - cylinder(r=5, h=30, center=True)
    - ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="difference2.png",
    size=wsize,
    yaw=yaw3,
    pitch=pitch3,
)

doscreen(
    model=sphere(r=10)
    ^ cylinder(r=5, h=30, center=True)
    ^ ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="intersect.png",
    size=wsize,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=sphere(r=10)
    ^ cylinder(r=5, h=30, center=True)
    ^ ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="intersect0.png",
    size=wsize,
    yaw=yaw1,
    pitch=pitch1,
)
doscreen(
    model=sphere(r=10)
    ^ cylinder(r=5, h=30, center=True)
    ^ ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="intersect1.png",
    size=wsize,
    yaw=yaw2,
    pitch=pitch2,
)
doscreen(
    model=sphere(r=10)
    ^ cylinder(r=5, h=30, center=True)
    ^ ngon(r=5, n=5).extrude(30, center=True).rotateX(deg(90)),
    path="intersect2.png",
    size=wsize,
    yaw=yaw3,
    pitch=pitch3,
)

# pnts = [(-5,-5), (0,0), (27,40), (25,50), (5,60), (-5,60)]
# tangs = [(1,1), (1,1), (0,0), (0,0), (0,0), (0,0)]
pnts = [(0, 0), (0, 10), (10, 20)]
tangs = [(0, 0), (0, 0), (1, 0)]
doscreen(model=[*points(pnts), interpolate(pnts)], path="interpolate0.png", size=wsize)
doscreen(
    model=[*points(pnts), interpolate(pnts, tangs=tangs)],
    path="interpolate1.png",
    size=wsize,
)
doscreen(
    model=[*points(pnts), interpolate(pnts, closed=True)],
    path="interpolate2.png",
    size=wsize,
)
doscreen(
    model=[*points(pnts), interpolate(pnts, tangs=tangs, closed=True)],
    path="interpolate3.png",
    size=wsize,
)

wire = sew(
    [
        segment((0, 0, 0), (0, 10, 0)),
        circle_arc((0, 10, 0), (10, 15, 0), (20, 10, 0)),
        segment((20, 0, 0), (20, 10, 0)),
        segment((20, 0, 0), (0, 0, 0)),
    ]
)

doscreen(model=wire, path="fill0.png", size=wsize)
doscreen(model=wire.fill(), path="fill1.png", size=wsize)

doscreen(model=cube(10), path="fillet0.png", size=wsize)
doscreen(
    model=[
        *points([(5, 0, 10), (5, 10, 10)]),
        cube(10).fillet(2, [(5, 0, 10), (5, 10, 10)]),
    ],
    path="fillet1.png",
    size=wsize,
)
doscreen(model=cube(10).fillet(2), path="fillet2.png", size=wsize)

doscreen(model=ngon(r=5, n=6), path="fillet3.png", size=wsize)
doscreen(
    model=[
        *points([(6, 0, 0), (-6, 0, 0)]),
        ngon(r=5, n=6).fillet(2, [(6, 0, 0), (-6, 0, 0)]),
    ],
    path="fillet4.png",
    size=wsize,
)
doscreen(model=ngon(r=5, n=6).fillet(2), path="fillet5.png", size=wsize)

doscreen(model=cube(10), path="chamfer0.png", size=wsize)
doscreen(
    model=[
        *points([(5, 0, 10), (5, 10, 10)]),
        cube(10).chamfer(2, [(5, 0, 10), (5, 10, 10)]),
    ],
    path="chamfer1.png",
    size=wsize,
)
doscreen(model=cube(10).chamfer(2), path="chamfer2.png", size=wsize)

pnts = points([(0, 0, 20), (20, 0, 20)])
doscreen(
    model=[(cylinder(r=10, h=20) - cylinder(r=5, h=20)).chamfer(r=1, refs=pnts), *pnts],
    path="chamfer3.png",
    size=wsize,
)

pnts = points([(5, 2.5, 2.5)])
doscreen(
    model=[thicksolid(cube(5), t=0.5, refs=pnts), *pnts],
    path="thicksolid0.png",
    size=wsize,
)
pnts = points([(5, 2.5, 2.5), (2.5, 2.5, 5)])
doscreen(
    model=[thicksolid(cube(5), t=0.5, refs=pnts), *pnts],
    path="thicksolid1.png",
    size=wsize,
)

yaw = math.pi * (7 / 16)
pitch = math.pi * -0.25

doscreen(
    model=ngon(r=10, n=10),
    path="extrude0.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=ngon(r=10, n=10).extrude(4),
    path="extrude1.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=ngon(r=10, n=10).extrude((1, 0, 4)),
    path="extrude2.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=textshape(
        text="TextShape", fontpath="../../zencad/examples/fonts/mandarinc.ttf", size=100
    ).extrude(20),
    path="extrude3.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)

r = 8
n = 3
doscreen(
    model=ngon(r=r, n=n),
    path="revol0.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=ngon(r=r, n=n).rotateX(deg(90)).right(30),
    path="revol1.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=revol(ngon(r=r, n=n).rotateX(deg(90)).right(30)),
    path="revol2.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=revol(ngon(r=r, n=n).rotateX(deg(90)).right(30), yaw=deg(120)),
    path="revol3.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)


pitch = math.pi * -0.10
wires = [
    circle(10, wire=True).up(30),
    circle(10, wire=True).up(20),
    circle(20, wire=True).up(10),
    circle(20, wire=True),
]

wires2 = [
    circle(10, wire=True).up(30),
    circle(10, wire=True).up(20),
    square(30, center=True, wire=True).up(10),
    square(30, center=True, wire=True),
]

doscreen(model=wires, path="loft0.png", size=wsize, triedron=True, yaw=yaw, pitch=pitch)
doscreen(
    model=loft(wires, smooth=False),
    path="loft1.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=loft(wires, smooth=True),
    path="loft2.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=wires2, path="loft3.png", size=wsize, triedron=True, yaw=yaw, pitch=pitch
)
doscreen(
    model=loft(wires2, smooth=False),
    path="loft4.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=loft(wires2, smooth=True),
    path="loft5.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)


pnts = points([(-5, -5), (0, 0), (27, 40), (25, 50), (5, 60), (-5, 60)])

tang = vectors([(1, 1), (1, 1), (0, 0), (0, 0), (0, 0), (0, 0)])

ps = [(20, 0, 0), (20, 0, 10), (30, 0, 5)]

spine = interpolate(pnts, tang).rotateX(deg(90))
profile = circle(3, wire=True).rotateY(deg(45)).translate(pnts[0].x, 0, pnts[0].y)
handle = pipe(path=spine, proto=profile)

pitch = math.pi * -0.20
yaw = math.pi * (7 / 16) + math.pi * 3 / 8
doscreen(
    model=[spine, profile],
    path="sweep0.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=sweep(profile, spine),
    path="sweep1.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=[polysegment(ps, closed=True), helix(h=100, r=20, step=30)],
    path="sweep2.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=sweep(
        polysegment(ps, closed=True), helix(h=100, r=20, step=30), frenet=False
    ),
    path="sweep3.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)
doscreen(
    model=sweep(polysegment(ps, closed=True), helix(h=100, r=20, step=30), frenet=True),
    path="sweep4.png",
    size=wsize,
    triedron=True,
    yaw=yaw,
    pitch=pitch,
)

doscreen(
    model=bezier([(0,0,0),(0,10,0),(0,10,10)]),
    path="bezier0.png",
    size=wsize
)

doscreen(
    model=bezier([(0,0,0),(0,10,0),(0,10,10)], [1,2,1]),
    path="bezier1.png",
    size=wsize
)

doscreen(
    model=section(box(10, center=True) - sphere(4)),
    path="section0.png",
    size=wsize
)

doscreen(
    model=section(box(10, center=True), sphere(7)),
    path="section1.png",
    size=wsize
)

doscreen(
    model=nulltrans()(box(10)),
    path="nulltrans01.png",
    size=wsize
)

m = zencad.internal_models.knight()
doscreen(
    model=(m, dock(80)),
    path="multitrans0.png",
    size=wsize
)

doscreen(
    model=(multitransform([ 
        translate(-20,20,0) * rotateZ(deg(60)),
        translate(-20,-20,0) * rotateZ(deg(120)),
        translate(20,20,0) * rotateZ(deg(180)),
        nulltrans()
    ])(m), dock(80)),
    path="multitrans1.png",
    size=wsize
)

P=-deg(60)
D=60

m = zencad.internal_models.knight()
doscreen(
    model=(m, dock(80)),
    path="complextrans0.png",
    size=wsize,
    pitch=P
)

doscreen(
    model=((moveX(20) * rotateZ(deg(60)))(m), dock(D)),
    path="complextrans1.png",
    size=wsize,
    pitch=P
)

trans = moveX(20) * rotateZ(deg(45))
m = zencad.internal_models.knight()

doscreen(
    model=((trans(m)), dock(D)),
    path="invtrans0.png",
    size=wsize,
    pitch=P
)

doscreen(
    model=((trans.inverse()(m)), dock(D)),
    path="invtrans1.png",
    size=wsize,
    pitch=P
)

trans = rotateZ(deg(45))
doscreen(
    model=((trans(m)), dock(D)),
    path="invtrans2.png",
    size=wsize,
    pitch=P
)

doscreen(
    model=((trans.inverse()(m)), dock(D)),
    path="invtrans3.png",
    size=wsize,
    pitch=P
)

doscreen(
    model=circle(10) - square(10),
    path="bool20.png",
    size=wsize, triedron=False
)

doscreen(
    model=circle(10) + square(10),
    path="bool21.png",
    size=wsize, triedron=False
)

doscreen(
    model=circle(10) ^ square(10),
    path="bool22.png",
    size=wsize, triedron=False
)

doscreen(
    model=section(circle(10), square(10)),
    path="bool23.png",
    size=wsize, triedron=False
)

m = cone(r1=5, r2=0, h=10, center=True).rotX(deg(45))
doscreen(
    model=((m, (1,0,0,0.6)), m ^ infplane()),
    path="infplane0.png",
    size=wsize
)

m = cone(r1=5, r2=0, h=10, center=True)
doscreen(
    model=((m, (1,0,0,0.6)), m ^ infplane()),
    path="infplane01.png",
    size=wsize
)

m = cone(r1=5, r2=0, h=10, center=True)
doscreen(
    model=((m, (1,0,0,0.6)), m ^ infplane().rotX(deg(45))),
    path="infplane1.png",
    size=wsize
)

m = cone(r1=5, r2=0, h=10, center=True)
doscreen(
    model=((m, (1,0,0,0.6)), m ^ infplane().rotY(deg(90)).right(2)),
    path="infplane2.png",
    size=wsize
)

doscreen(
    model=zencad.platonic.platonic(4,10),
    path="platonic0.png",
    size=wsize
)

doscreen(
    model=zencad.platonic.platonic(6,10),
    path="platonic1.png",
    size=wsize
)

doscreen(
    model=zencad.platonic.platonic(8,10),
    path="platonic2.png",
    size=wsize
)

doscreen(
    model=zencad.platonic.platonic(12,10),
    path="platonic3.png",
    size=wsize
)

doscreen(
    model=zencad.platonic.platonic(20,10),
    path="platonic4.png",
    size=wsize
)


doscreen(
    model=offset(cone(r1=15,r2=10,h=20), r=5),
    path="offset0.png",
    size=wsize
)

doscreen(
    model=(
        rounded_polysegment([(0,0,0), (20,0,0), (20,20,40), (-40,20,40), (-40,20,0)], 10), 
        *points([(0,0,0), (20,0,0), (20,20,40), (-40,20,40), (-40,20,0)])
    ),
    path="rounded_polysegment0.png",
    size=wsize,
    yaw=deg(160-90-30)
)


import zencad.draw as draw
doscreen(
    model=(
        zencad.internal_models.knight(), 
        draw.arrow((0,0,0), vector3(1,1,1).normalize()*30, clr=color.blue, scene=None), 
        draw.arrow((0,0,0), vector3(0,0,1).normalize()*30, clr=color.green, scene=None)),
    path="short_rotate0.png",
    size=wsize
)

A = -40
doscreen(
    model=ruled(circle(r=20, wire=True), circle(r=20, wire=True).up(20)),
    path="ruled0.png",
    size=wsize,
    pitch=deg(A)
)


doscreen(
    model=ruled(circle(r=20, wire=True), circle(r=20, wire=True).rotZ(math.pi/2*3).up(20)),
    path="ruled1.png",
    size=wsize,
    pitch=deg(A)
)


doscreen(
    model=ruled(
        interpolate([(0,0),(-4,10),(4,20),(-6,30),(6,40)]),
        interpolate([(0,0),(-2,10),(2,20),(-4,30),(4,40)]).up(20),
        ),
    path="ruled2.png",
    size=wsize,
    pitch=deg(A),
    yaw=deg(45)
)

doscreen(
    model=ruled(
        interpolate([(0,0),(-4,10),(4,20),(-6,30),(6,40)]),
        interpolate([(0,0),(-2,10),(2,20),(-4,30),(4,40)]).up(20),
        ),
    path="ruled3.png",
    size=wsize,
    pitch=deg(A),
    yaw=deg(0)
)

knight = zencad.internal_models.knight()
doscreen(
    model=knight.move(20,20),
    path="rotate_array0.png",
    size=wsize
)

doscreen(
    model=rotate_array(6, yaw=deg(270), endpoint=True)(knight.move(20,20)),
    path="rotate_array1.png",
    size=wsize
)


knight = zencad.internal_models.knight()
doscreen(
    model=square(10, center=True, wire=True),
    path="rotate_array20.png",
    size=wsize
)

doscreen(
    model=rotate_array2(n=60, r=20, yaw=(0,deg(270)), roll=(0,deg(360)), array=True)(square(10, center=True, wire=True)),
    path="rotate_array21.png",
    size=wsize
)

knight = zencad.internal_models.knight()
doscreen(
    model=knight.move(20,30),
    path="sqrmirror0.png",
    size=wsize
)

doscreen(
    model=sqrmirror()(knight.move(20,30)),
    path="sqrmirror1.png",
    size=wsize
)

doscreen(
    model=revol2(profile=square(10, center=True), r=20, n=60, yaw=(0,deg(360)), roll=(0,deg(360))),
    path="revol20.png",
    size=wsize
)