#!/usr/bin/env python3

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from zencad.settings import Settings


class Color:
    def test_value(self, val):
        if val < 0 or val > 1:
            raise Exception(
                f"Wrong color parameter. It must be in range [0..1]. val={val}")

    def __init__(self, r, g=None, b=None, a=0):
        if g is None:
            g = r[1]
            b = r[2]
            if len(r) >= 4:
                a = r[3]
            r = r[0]

        self.r = r
        self.g = g
        self.b = b
        self.a = a

        self.test_value(r)
        self.test_value(g)
        self.test_value(b)
        self.test_value(a)

    def __getitem__(self, i):
        if i == 0:
            return self.r
        elif i == 1:
            return self.g
        elif i == 2:
            return self.b
        else:
            return self.a

    def __len__(self):
        return 4

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
Color.brown = Color(0.396,  0.263, 0.129)
Color.grey = Color(0.325,  0.337, 0.329)
#Color.red = Color(1, 0, 0)
#Color.green = Color(0, 1, 0)
#Color.blue = Color(0, 0, 1)
#Color.yellow = Color(1, 1, 0)
Color.red = Color(0.669,  0.18,  0.09)
Color.blue = Color(0.059, 0.298, 0.506)
Color.green = Color(0.294,  0.595,  0.231)
Color.yellow = Color(1,  0.898,  0.486)  # gold
Color.magenta = Color(1, 0, 1)
Color.cian = Color(0, 1, 1)
Color.mech = Color(0.6, 0.6, 0.8)
Color.transmech = Color(0.6, 0.6, 0.8, 0.8)
Color.orange = Color(1, 0xa5/255, 0)

white = Color.white
black = Color.black
red = Color.red
green = Color.green
blue = Color.blue
yellow = Color.yellow
magenta = Color.magenta
cian = Color.cian
mech = Color.mech
transmech = Color.transmech
orange = Color.orange


def default_color():
    return Color(Settings.get(["view", "default_color"]))

_default_wire_color = Color(0, 0, 0)
def default_wire_color():
    return _default_wire_color

_default_border_color = Color(0, 0, 0)
def default_border_color():
    return _default_border_color

_default_point_color = Color(0, 1, 0)
def default_point_color():
    return  _default_point_color

def set_default_point_color(color):
    global _default_point_color
    _default_point_color = color    

def set_default_wire_color(color):
    global _default_wire_color
    _default_wire_color = color    

def set_default_border_color(color):
    global _default_border_color
    _default_border_color = color    