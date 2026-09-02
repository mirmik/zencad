import math
import unittest

from OCP.TopAbs import TopAbs_SHELL, TopAbs_SOLID

from zencad import geom as typed


class TypedLegacyAliasCompatibilityTest(unittest.TestCase):
    def setUp(self):
        self.context = typed.Context.deferred(cache=False)

    def test_legacy_aliases_materialize_the_same_geometry(self):
        context = self.context
        sections = (
            context.call(typed.circle, 2, wire=True),
            context.call(typed.circle, 3, wire=True).up(4),
        )
        canonical_loft = context.call(
            typed.loft,
            sections,
            smooth=True,
            shell=True,
            max_degree=6,
        )
        legacy_loft = context.call(
            typed.loft,
            sections,
            smooth=True,
            shell=True,
            maxdegree=6,
        )

        solid = context.call(typed.box, 4)
        canonical_thick = context.call(
            typed.thicksolid,
            solid,
            -0.25,
            [(2, 2, 4)],
        )
        legacy_thick = context.call(
            typed.thicksolid,
            solid,
            t=-0.25,
            refs=[(2, 2, 4)],
        )

        profile = context.call(typed.square, 1, center=True)
        canonical_revol = context.call(
            typed.revol2,
            profile,
            3,
            sections=12,
            yaw=(0, math.pi),
        )
        legacy_revol = context.call(
            typed.revol2,
            profile=profile,
            r=3,
            n=12,
            yaw=(0, math.pi),
        )

        pipe_profile = context.call(typed.circle, 0.5, wire=True)
        spine = context.call(typed.segment, (0, 0), (0, 0, 4))
        canonical_pipe = context.call(typed.pipe_shell, [pipe_profile], spine)
        legacy_pipe = context.call(
            typed.pipe_shell,
            arr=[pipe_profile],
            spine=spine,
        )

        self.assertEqual(canonical_loft.native().ShapeType(), TopAbs_SHELL)
        self.assertEqual(legacy_loft.native().ShapeType(), TopAbs_SHELL)
        for canonical, legacy in (
            (canonical_thick, legacy_thick),
            (canonical_revol, legacy_revol),
            (canonical_pipe, legacy_pipe),
        ):
            self.assertEqual(canonical.native().ShapeType(), TopAbs_SOLID)
            self.assertEqual(legacy.native().ShapeType(), TopAbs_SOLID)
            self.assertAlmostEqual(canonical.mass().value(), legacy.mass().value())

    def test_alias_conflicts_fail_explicitly_at_materialization(self):
        context = self.context
        first = context.call(typed.circle, 1, wire=True)
        second = first.up(2)
        solid = context.call(typed.box, 2)
        profile = context.call(typed.square, 1)
        spine = context.call(typed.segment, (0, 0), (0, 0, 2))

        conflicts = (
            context.call(
                typed.loft,
                (first, second),
                max_degree=4,
                maxdegree=5,
            ),
            context.call(
                typed.thicksolid,
                solid,
                -0.1,
                [(1, 1, 2)],
                t=-0.2,
            ),
            context.call(typed.revol2, profile, 2, r=3),
            context.call(
                typed.pipe_shell,
                [first],
                spine,
                arr=[first],
            ),
        )

        for result in conflicts:
            with self.subTest(operation=result._state.operation_id):
                with self.assertRaisesRegex(TypeError, "cannot both be provided"):
                    result.native()


if __name__ == "__main__":
    unittest.main()
