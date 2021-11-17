from OCC.Core.Bnd import Bnd_Box


class BoundaryBox:
    def __init__(self, xl=None, xh=None, yl=None, yh=None, zl=None, zh=None):
        if isinstance(xl, Bnd_Box):
            self.assign_Bnd_Box(xl)
            return

        if (xl is None):
            self.assign_coords(0, 0, 0, 0, 0, 0)
            self.inited = False
            return

        self.assign_coords(xl, xh, yl, yh, zl, zh)

    def assign_coords(self, xl, xh, yl, yh, zl, zh):
        self.xmin = xl
        self.xmax = xh
        self.ymin = yl
        self.ymax = yh
        self.zmin = zl
        self.zmax = zh
        self.inited = True

    def assign(self, box):
        self.xmin = box.xmin
        self.xmax = box.xmax
        self.ymin = box.ymin
        self.ymax = box.ymax
        self.zmin = box.zmin
        self.zmax = box.zmax
        self.inited = True

    def assign_Bnd_Box(self, Box):
        a, b, c, d, e, f = Box.Get()
        self.xmin = a
        self.xmax = d
        self.ymin = b
        self.ymax = e
        self.zmin = c
        self.zmax = f
        self.inited = True

    def add(self, bbox):
        if self.inited is False:
            self.assign(bbox)

        else:
            self.xmin = min(self.xmin, bbox.xmin)
            self.ymin = min(self.ymin, bbox.ymin)
            self.zmin = min(self.zmin, bbox.zmin)
            self.xmax = max(self.xmax, bbox.xmax)
            self.ymax = max(self.ymax, bbox.ymax)
            self.zmax = max(self.zmax, bbox.zmax)

    def xrange(self): return (self.xmin, self.xmax)
    def yrange(self): return (self.ymin, self.ymax)
    def zrange(self): return (self.zmin, self.zmax)

    def xlength(self): return self.xmax - self.xmin
    def ylength(self): return self.ymax - self.ymin
    def zlength(self): return self.zmax - self.zmin

    def shape(self):
        from zencad.geom.solid import box
        return box(self.xlength(), self.ylength(), self.zlength()).move(self.xmin, self.ymin, self.zmin)
