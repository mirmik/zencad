import unittest
import zencad
from functools import cmp_to_key
import evalcache
import zencad.util
import os

import tempfile


class ConvertProbe(unittest.TestCase):
    def setUp(self):
        zencad.lazy.encache = False
        zencad.lazy.decache = False
        zencad.lazy.fastdo = True

    def test_stl_probe(self):
        zencad.to_stl(zencad.box(10), os.path.join(
            tempfile.gettempdir(), "tempstl.stl"), 0.01)

    def test_brep_probe(self):
        zencad.to_brep(zencad.box(10), os.path.join(
            tempfile.gettempdir(), "tempbrep.brep"))
        m = zencad.from_brep(os.path.join(
            tempfile.gettempdir(), "tempbrep.brep"))

        self.assertEqual(len(m.unlazy().vertices()), 8)
