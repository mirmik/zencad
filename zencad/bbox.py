from OCC.Core.Bnd import Bnd_Box


class BoundaryBox:
    def __init__(self, xl, xh, yl, yh, zl, zh):
        self.xmin = xl
        self.xmax = xh
        self.ymin = yl
        self.ymax = yh
        self.zmin = zl
        self.zmax = zh

    def xrange(self): return (self.xmin, self.xmax)
    def yrange(self): return (self.ymin, self.ymax)
    def zrange(self): return (self.zmin, self.zmax)

    def xlength(self): return self.xmax - self.xmin
    def ylength(self): return self.ymax - self.ymin
    def zlength(self): return self.zmax - self.zmin

    def shape(self):
        from zencad.geom.solid import box
        return box(self.xlength(), self.ylength(), self.zlength()).move(self.xmin, self.ymin, self.zmin)
