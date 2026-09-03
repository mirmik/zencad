from pathlib import Path
import subprocess
import sys
import unittest

from evalcache import EvaluationEventKind, EvaluationMode
from OCP.Standard import Standard_ConstructionError

import zencad
from zencad.operation import resolve_context, using_context


ROOT = Path(__file__).parents[1]


class EvaluationPolicyTest(unittest.TestCase):
    def test_public_class_is_independent_of_mode_and_cache(self):
        for mode in EvaluationMode:
            for cache in (False, True):
                with self.subTest(mode=mode.value, cache=cache):
                    with zencad.evaluation(mode, cache=cache):
                        self.assertIs(type(zencad.box(1)), zencad.Solid)

    def test_eager_evaluates_during_construction_without_changing_type(self):
        events = []
        owner = zencad.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        with using_context(owner):
            with zencad.deferred() as deferred_context:
                deferred_shape = zencad.box(2)
                self.assertEqual(events, [])

            with zencad.eager() as eager_context:
                eager_shape = zencad.box(2)

        self.assertIs(type(deferred_shape), zencad.Solid)
        self.assertIs(type(eager_shape), zencad.Solid)
        self.assertIs(deferred_shape.context, deferred_context)
        self.assertIs(eager_shape.context, eager_context)
        self.assertTrue(
            any(
                event.kind is EvaluationEventKind.FINISH
                and event.operation_id == "zencad.typed.box"
                for event in events
            )
        )

    def test_nested_policies_restore_the_exact_outer_context(self):
        original = resolve_context()

        with zencad.evaluation("immediate", cache=False) as outer:
            self.assertIs(resolve_context(), outer)
            self.assertIs(zencad.evaluation_mode(), EvaluationMode.IMMEDIATE)
            self.assertFalse(outer.cache_enabled)
            with zencad.deferred() as inner:
                self.assertIs(resolve_context(), inner)
                self.assertIs(zencad.evaluation_mode(), EvaluationMode.DEFERRED)
                self.assertFalse(inner.cache_enabled)
            self.assertIs(resolve_context(), outer)
            self.assertIs(zencad.evaluation_mode(), EvaluationMode.IMMEDIATE)

            with self.assertRaisesRegex(RuntimeError, "leave inner policy"):
                with zencad.deferred(cache=True):
                    raise RuntimeError("leave inner policy")
            self.assertIs(resolve_context(), outer)
            self.assertIs(zencad.evaluation_mode(), EvaluationMode.IMMEDIATE)

        self.assertIs(resolve_context(), original)
        self.assertIs(zencad.evaluation_mode(), original.mode)

    def test_immediate_alias_and_argument_validation(self):
        with zencad.immediate(cache=False) as context:
            self.assertIs(context.mode, EvaluationMode.IMMEDIATE)
        with self.assertRaises(ValueError):
            with zencad.evaluation("eventually"):
                pass
        with self.assertRaises(TypeError):
            with zencad.eager(cache=1):
                pass

    def test_eager_reports_geometry_errors_at_the_declaring_operation(self):
        with zencad.deferred(cache=False):
            deferred_shape = zencad.sphere(-1)
        with self.assertRaises(Standard_ConstructionError):
            deferred_shape.native()

        with self.assertRaises(Standard_ConstructionError):
            with zencad.eager(cache=False):
                zencad.sphere(-1)

    def test_fresh_process_policy_is_qt_free(self):
        process = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys, zencad; "
                    "assert not any(n.startswith('PyQt5') for n in sys.modules); "
                    "assert zencad.evaluation_mode().value == 'deferred'; "
                    "outer = zencad.eager(cache=False); "
                    "context = outer.__enter__(); "
                    "shape = zencad.box(2); "
                    "assert type(shape) is zencad.Solid; "
                    "assert shape.context is context; "
                    "assert context.mode.value == 'immediate'; "
                    "assert not context.cache_enabled; "
                    "outer.__exit__(None, None, None); "
                    "assert zencad.evaluation_mode().value == 'deferred'; "
                    "assert not any(n.startswith('PyQt5') for n in sys.modules)"
                ),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(process.returncode, 0, process.stderr)


if __name__ == "__main__":
    unittest.main()
