#!/usr/bin/env python3
# coding: utf-8

from zencad import *

tetra = tetrahedron(10)
hexa = hexahedron(10)
octa = octahedron(10)
dodeca = dodecahedron(10)
icosa = icosahedron(10)

disp(tetra)
disp(hexa.movX(20))
disp(octa.movX(40))
disp(dodeca.movX(60))
disp(icosa.movX(80))

show()
