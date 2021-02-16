#!/usr/bin/env python3

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB


class Color:
    def test_value(self, val):
        if val < 0 or val > 1:
            raise Exception(
                f"Wrong color parameter. It must be in range [0..1]. val={val}")

    def __init__(self, r, g, b, a=0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

        self.test_value(r)
        self.test_value(g)
        self.test_value(b)
        self.test_value(a)

    def to_QColor(self):
        import PyQt5.QtGui
        return PyQt5.QtGui.QColor(self.r, self.g, self.b, self.a)

    def to_Quantity_Color(self):
        return Quantity_Color(self.r, self.g, self.b, Quantity_TOC_RGB)

    def __repr__(self):
        return f"Color({self.r},{self.g},{self.b},{self.a})"

    def __str__(self):
        return f"({self.r},{self.g},{self.b},{self.a})"


Color.white = Color(1, 1, 1)
Color.black = Color(0, 0, 0)
Color.red = Color(1, 0, 0)
Color.green = Color(0, 1, 0)
Color.blue = Color(0, 0, 1)
Color.yellow = Color(1, 1, 0)
Color.magenta = Color(1, 0, 1)
Color.cian = Color(0, 1, 1)
Color.mech = Color(0.6, 0.6, 0.8)
Color.transmech = Color(0.6, 0.6, 0.8, 0.8)
Color.orange = Color(1, 0xa5/255, 0)


def default_color():
    return Color.mech


def default_wire_color():
    return Color(1, 1, 1)
    # return Color(int("0x92",0)/255, int("0x6E",0)/255, int("0xAE",0)/255)
