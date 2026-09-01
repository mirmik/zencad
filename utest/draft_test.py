import unittest

import zencad
from zencad import _typed as typed
from zencad.geom.shape import LazyObjectShape


ANGLE = zencad.deg(5)


class DraftTest(unittest.TestCase):
    def setUp(self):
        self.cache_flags = (zencad.lazy.encache, zencad.lazy.decache)
        zencad.lazy.encache = False
        zencad.lazy.decache = False

    def tearDown(self):
        zencad.lazy.encache, zencad.lazy.decache = self.cache_flags

    def test_positive_and_negative_angles_taper_multiple_faces(self):
        body = zencad.box(10)
        side_faces = body.faces()[:4]

        positive = zencad.draft(body, side_faces, ANGLE)
        negative = zencad.draft(body, side_faces, -ANGLE)

        self.assertIsInstance(positive, LazyObjectShape)
        self.assertAlmostEqual(float(positive.mass()), 835.2283612755552)
        self.assertAlmostEqual(float(negative.mass()), 1185.1830153792514)
        self.assertLess(float(positive.mass()), 1000)
        self.assertGreater(float(negative.mass()), 1000)

    def test_neutral_face_and_origin_normal_are_equivalent(self):
        body = zencad.box(10)
        side = body.faces()[2]
        from_tuple = zencad.draft(
            body,
            side,
            ANGLE,
            neutral=((0, 0, 5), (0, 0, 1)),
        )
        from_face = zencad.draft(
            body,
            side,
            ANGLE,
            neutral=zencad.infplane().up(5),
        )

        self.assertAlmostEqual(float(from_tuple.mass()), 1000)
        self.assertAlmostEqual(float(from_face.mass()), 1000)
        self.assertEqual(
            sorted(tuple(round(value, 6) for value in point) for point in from_tuple.unlazy().vertices()),
            sorted(tuple(round(value, 6) for value in point) for point in from_face.unlazy().vertices()),
        )

    def test_draft_is_lazy_and_rejects_invalid_inputs_diagnostically(self):
        body = zencad.box(10)
        side = body.faces()[0]
        first = zencad.draft(body, side, ANGLE)
        repeated = zencad.draft(body, side, ANGLE)
        self.assertEqual(first.__lazyhexhash__, repeated.__lazyhexhash__)

        with self.assertRaisesRegex(ValueError, "at least one face"):
            zencad.draft(body, (), ANGLE).unlazy()
        with self.assertRaisesRegex(ValueError, "non-zero"):
            zencad.draft(body, side, 0).unlazy()
        with self.assertRaisesRegex(ValueError, "rejected face 1"):
            zencad.draft(body, zencad.box(1).faces()[0], ANGLE).unlazy()

    def test_typed_draft_preserves_solid_and_context(self):
        context = typed.Context.deferred(cache=False)
        with typed.using_context(context):
            body = typed.box(10)
            side_faces = tuple(body.faces()[index] for index in range(4))
            positive = typed.draft(body, side_faces, ANGLE)
            negative = typed.draft(body, side_faces, -ANGLE)

        self.assertIs(type(positive), typed.Solid)
        self.assertIs(positive.runtime, context)
        self.assertAlmostEqual(float(positive.mass()), 835.2283612755552)
        self.assertAlmostEqual(float(negative.mass()), 1185.1830153792514)


if __name__ == "__main__":
    unittest.main()
