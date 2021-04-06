from zencad.util import point3, vector3
from zencad.geom.wire import *
# from zencad.geom. import *

import zencad.gutil
from zencad.util import deg

import math


class wire_builder:
    def __init__(self, start=(0, 0, 0), defrel=False):
        self.edges = []
        self.current = point3(start)
        self.start = self.current
        self.default_rel = defrel

    def restart(self, pnt, y=None, z=None):
        pnt = self.collect_point(pnt, y, z)
        self.edges = []
        self.current = point3(pnt)
        self.start = self.current
        return self

    @staticmethod
    def collect_point(pnt, y, z):
        if z is not None:
            pnt = (pnt, y, z)
        elif y is not None:
            pnt = (pnt, y)
        return pnt

    def prepare(self, pnts, rel):
        if rel is None:
            rel = self.default_rel

        if rel is False:
            return points(pnts)
        else:
            return [self.current + vector3(p) for p in pnts]

    def segment(self, pnt, y=None, z=None, rel=None):
        pnt = self.collect_point(pnt, y, z)
        target, = self.prepare([pnt], rel)
        self.edges.append(segment(self.current, target))
        self.current = target
        return self

    def line(self, *args, **kwargs):
        return self.segment(*args, **kwargs)

    def l(self, *args, **kwargs):
        return self.segment(*args, **kwargs)

    def plane_circle_arc(self, r, angle, large, sweep, x, y):
        centers = zencad.gutil.restore_circle_centers(
            self.current, point3(x, y), r)
        target = point3(x, y)

        cent = None

        if centers[0].early(centers[1]):
            cent = centers[0]

            if sweep:
                self.arc(cent, r, deg(180))
            else:
                self.arc(cent, r, -deg(180))

        else:
            for c in centers:

                cv = self.current - c
                tv = target - c

                angle = cv.angle(tv)
                if cv.cross(tv).z < 0:
                    angle = -angle

                if large:
                    if angle <= 0:
                        angle += math.pi * 2
                    else:
                        angle -= math.pi * 2

                if angle >= 0 and sweep is True:
                    self.arc(c, r, angle)

                if angle < 0 and sweep is False:
                    self.arc(c, r, angle)

    def svg_elliptic_arc(self,
                         rx,
                         ry,
                         x_axis_angle,
                         large,
                         sweep,
                         x,
                         y):

        centers = zencad.gutil.restore_ellipse_centers(
            self.current, point3(x, y), rx, ry, x_axis_angle)
        target = point3(x, y)

        for cent in centers:
            full_edge = zencad.ellipse(rx, ry, wire=True) \
                .rotZ(x_axis_angle)            \
                .mov(cent)

            start_point_parameter = full_edge.lower_distance_parameter(
                self.current)
            finish_point_parameter = full_edge.lower_distance_parameter(target)

            diff = finish_point_parameter - start_point_parameter

            if not sweep:
                if diff < 0:
                    diff += 2*math.pi
                if start_point_parameter > finish_point_parameter:
                    start_point_parameter -= 2*math.pi

                assert start_point_parameter < finish_point_parameter
            else:
                if diff > 0:
                    diff -= 2*math.pi
                if start_point_parameter < finish_point_parameter:
                    start_point_parameter += 2*math.pi

                assert start_point_parameter > finish_point_parameter

            if abs(diff) < math.pi and large:
                continue

            if abs(diff) > math.pi and not large:
                continue
            if not sweep:
                trimmed = full_edge.trimmed_edge(
                    start_point_parameter, finish_point_parameter)
            else:
                trimmed = full_edge.trimmed_edge(
                    finish_point_parameter, start_point_parameter)

            self.edges.append(trimmed)
            break

        self.current = target

    def svg_circle_arc(self,
                       r,
                       x_axis_angle,
                       large,
                       sweep,
                       x,
                       y):

        centers = zencad.gutil.restore_circle_centers(
            self.current, point3(x, y), r)
        target = point3(x, y)

        for cent in centers:
            full_edge = zencad.circle(r, wire=True) \
                .rotZ(x_axis_angle)            \
                .mov(cent)

            start_point_parameter = full_edge.lower_distance_parameter(
                self.current)
            finish_point_parameter = full_edge.lower_distance_parameter(target)

            diff = finish_point_parameter - start_point_parameter

            if not sweep:
                if diff < 0:
                    diff += 2*math.pi
                if start_point_parameter > finish_point_parameter:
                    start_point_parameter -= 2*math.pi

                assert start_point_parameter < finish_point_parameter
            else:
                if diff > 0:
                    diff -= 2*math.pi
                if start_point_parameter < finish_point_parameter:
                    start_point_parameter += 2*math.pi

                assert start_point_parameter > finish_point_parameter

            if abs(diff) < math.pi and large:
                continue

            if abs(diff) > math.pi and not large:
                continue

            if not sweep:
                trimmed = full_edge.trimmed_edge(
                    start_point_parameter, finish_point_parameter)
            else:
                trimmed = full_edge.trimmed_edge(
                    finish_point_parameter, start_point_parameter)

            self.edges.append(trimmed)
            break

        self.current = target

    # @angle - x-axis rotation
    # def plane_elliptic_arc(self, rx, ry, x_axis_angle, large, sweep, x, y):
    #	centers = zencad.gutil.restore_ellipse_centers(self.current, point3(x,y), rx, ry, x_axis_angle)
    #	target = point3(x,y)
#
    #	print("CENTERS", centers)
#
    #	cent = None
#
    #	if centers[0].early(centers[1]):
    #		cent = centers[0]
#
    #		if sweep:
    #			self.elliptic_arc(cent, rx, ry, deg(180))
    #		else:
    #			self.elliptic_arc(cent, rx, ry, -deg(180))
#
    #	else:
    #		for c in centers:
    #			cv = self.current - c
    #			tv = target - c
#
    #			angle = cv.angle(tv)
    #			if cv.cross(tv).z < 0: angle = -angle
#
    #			if large:
    #				if angle <= 0:
    #					angle += math.pi * 2
    #				else:
    #					angle -= math.pi * 2
#
    #			if angle >= 0 and sweep is True:
    #				self.elliptic_arc(c, rx, ry, angle, x_axis_angle)
#
    #			if angle < 0 and sweep is False:
    #				self.elliptic_arc(c, rx, ry, angle, x_axis_angle)

    def close(self, approx_a=False, approx_b=False):
        if self.current.distance(self.start) < 1e-5:
            return

        if not approx_a and not approx_b:
            self.edges.append(segment(self.current, self.start))

        else:
            tanga = (0, 0, 0)
            tangb = (0, 0, 0)

            if approx_a:
                tanga = self.edges[-1].d1(self.edges[-1].range()[1])

            if approx_b:
                tangb = self.edges[0].d1(self.edges[0].range()[0])

            self.edges.append(interpolate(
                [self.current, self.start], [tanga, tangb]))

        return self

    def arc_by_points(self, a, b, rel=None):
        a, b = self.prepare([a, b], rel)
        self.edges.append(circle_arc(self.current, a, b))
        self.current = b
        return self

    def arc(self, c, r, angle, rel=None):
        c, = self.prepare([c], rel)
        v = self.current - c

        vangle = v.angle((1, 0, 0))
        if zencad.vector3(1, 0, 0).cross(v).z < 0:
            vangle = - vangle

        shp = zencad.circle(r, angle=angle, wire=True).rotZ(
            vangle).mov(vector3(c))
        self.edges.append(shp)
        ep = shp.endpoints().unlazy()
        self.current = ep[1] if angle >= 0 else ep[0]
        return self

    def elliptic_arc(self, c, r1, r2, angle, rotate, rel=None):
        c, = self.prepare([c], rel)
        v = self.current - c

        vangle = v.angle((1, 0, 0))
        if zencad.vector3(1, 0, 0).cross(v).z < 0:
            vangle = - vangle

        shp = (zencad.ellipse(r1, r2, angle=angle, wire=True)
               .rotZ(vangle).mov(vector3(c)))

        self.edges.append(shp)
        ep = shp.endpoints().unlazy()
        self.current = ep[1] if angle >= 0 else ep[0]
        return self

    def interpolate(self, pnts, tangs=None, curtang=(0, 0, 0), approx=False, rel=None):
        if tangs is None:
            tangs = [(0, 0, 0)] * len(pnts)

        if approx:
            cc, fintang = self.edges[-1].d1(self.edges[-1].range()[1])
            curtang = fintang

        pnts = self.prepare(pnts, rel)
        pnts = points([self.current] + pnts)
        tangs = vectors([curtang] + tangs)

        self.edges.append(interpolate(pnts=pnts, tangs=tangs))
        self.current = pnts[-1]
        return self

    def doit(self):
        if len(self.edges) == 0:
            raise Exception("WireBuilder: No one edge here.")
        return sew(self.edges)
