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
