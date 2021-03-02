from OCC.Core.Bnd import Bnd_Box


class BoundaryBox:
    def __init__(self, xl, xh, yl, yh, zl, zh):
        self.x = (xl, xh)
        self.y = (yl, yh)
        self.z = (zl, zh)

    def xrange(self): return self.x
    def yrange(self): return self.y
    def zrange(self): return self.z

    def xmin(self): return self.x[0]
    def ymin(self): return self.y[0]
    def zmin(self): return self.z[0]

    def xmax(self): return self.x[1]
    def ymax(self): return self.y[1]
    def zmax(self): return self.z[1]
