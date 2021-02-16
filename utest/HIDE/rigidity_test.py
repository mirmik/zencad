import unittest
import zencad
import zencad.libs.rigidity
import numpy
import math


class Rigidity(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_rigidity_matrix_symmetric(self):
        E = 1
        G = 2
        F = 3
        Jx = 4
        Jy = 5
        Jz = 6
        l = 7

        mat = zencad.libs.rigidity.rod_rigidity_matrix(E, G, F, Jx, Jy, Jz, l)

        for i in range(6):
            for j in range(6):
                self.assertEqual(mat[i, j], mat[j, i])
