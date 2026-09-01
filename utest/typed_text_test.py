from pathlib import Path
import unittest

from evalcache.v2 import EvaluationEventKind, EvaluationMode, MemoryCacheStore

import zencad
from zencad import geom as typed
from zencad.operation import DomainOperation, using_context


FONT_PATH = (
    Path(zencad.__file__).resolve().parent / "examples" / "fonts" / "mandarinc.ttf"
)


class TypedTextTest(unittest.TestCase):
    def test_text_family_is_declared_at_module_level(self):
        self.assertIsInstance(typed.text_to_brep, DomainOperation)

        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        typed.register_font(FONT_PATH)
        with using_context(context):
            text = typed.text_to_brep("Text", "MandarinC", 10)
            alias = typed.textshape("Alias", "MandarinC", 10)

        self.assertIs(type(text), typed.Compound)
        self.assertIs(type(alias), typed.Compound)
        self.assertIs(text.context, context)
        self.assertIs(alias.context, context)
        self.assertEqual(text._state.operation_id, "zencad.typed.text_to_brep")
        self.assertEqual(alias._state.operation_id, "zencad.typed.text_to_brep")
        self.assertEqual(events, [])

    def test_text_factories_are_policy_independent(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    events = []
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                        progress_hooks=(events.append,),
                    )
                    context.call(typed.register_font, FONT_PATH)
                    text = context.call(
                        typed.text_to_brep,
                        "Hello, Мир",
                        "MandarinC",
                        20,
                    )
                    legacy_text = context.call(
                        typed.textshape,
                        "A",
                        "MandarinC",
                        10,
                        composite_curve=True,
                    )

                    observed_types.add((type(text), type(legacy_text)))
                    self.assertIs(type(text), typed.Compound)
                    self.assertIs(type(legacy_text), typed.Compound)
                    if mode is EvaluationMode.DEFERRED:
                        self.assertEqual(events, [])

                    self.assertEqual(text.shapetype(), "compound")
                    self.assertEqual(legacy_text.shapetype(), "compound")
                    self.assertGreater(len(text.edges()), 0)
                    self.assertGreater(len(legacy_text.edges()), 0)
                    bounds = text.boundbox().value()
                    self.assertGreater(bounds.xmax - bounds.xmin, 50)
                    self.assertGreater(bounds.ymax - bounds.ymin, 10)

        self.assertEqual(len(observed_types), 1)

    def test_font_registration_is_immediate_but_text_size_preserves_the_graph(self):
        events = []
        context = typed.Context.deferred(cache=False, progress_hooks=(events.append,))
        context.call(typed.register_font, FONT_PATH, typed.FontAspect.UNDEFINED)
        self.assertEqual(events, [])

        size = context.call(typed.box, 2).mass() * 2.5
        text = context.call(
            typed.text_to_brep,
            "Graph",
            "MandarinC",
            size,
            typed.FontAspect.REGULAR,
        )
        self.assertEqual(events, [])
        self.assertIs(type(text), typed.Compound)
        self.assertGreater(len(text.edges()), 0)
        self.assertTrue(events)

    def test_process_font_state_keeps_text_expressions_out_of_the_cache(self):
        store = MemoryCacheStore()

        first_events = []
        first = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(first_events.append,),
        )
        first.call(typed.register_font, FONT_PATH)
        self.assertGreater(
            len(first.call(typed.textshape, "A", "MandarinC", 10).edges()), 0
        )
        self.assertFalse(
            any(
                event.kind is EvaluationEventKind.CACHE_STORE
                and event.operation_id == "zencad.typed.text_to_brep"
                for event in first_events
            )
        )

        second_events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(second_events.append,),
        )
        second.call(typed.register_font, FONT_PATH)
        self.assertGreater(
            len(second.call(typed.textshape, "A", "MandarinC", 10).edges()), 0
        )
        self.assertFalse(
            any(
                event.kind is EvaluationEventKind.CACHE_HIT
                and event.operation_id == "zencad.typed.text_to_brep"
                for event in second_events
            )
        )

    def test_invalid_inputs_fail_at_the_correct_boundary(self):
        context = typed.Context.deferred(cache=False)

        with self.assertRaises(FileNotFoundError):
            context.call(typed.register_font, FONT_PATH.with_name("missing.ttf"))
        with self.assertRaisesRegex(TypeError, "str or PathLike"):
            context.call(typed.register_font, 3)  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "must be FontAspect"):
            context.call(typed.register_font, FONT_PATH, "regular")  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "text must be str"):
            context.call(typed.text_to_brep, 3, "MandarinC", 10).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "font_name must be str"):
            context.call(typed.text_to_brep, "A", 3, 10).native()  # type: ignore[arg-type]
        with self.assertRaisesRegex(TypeError, "composite_curve must be bool"):
            context.call(
                typed.text_to_brep, "A", "MandarinC", 10, composite_curve=1
            ).native()  # type: ignore[arg-type]

        context.call(typed.register_font, FONT_PATH)
        with self.assertRaisesRegex(ValueError, "size must be finite and positive"):
            context.call(typed.textshape, "A", "MandarinC", 0).native()
        immediate = typed.Context.immediate(cache=False)
        immediate.call(typed.register_font, FONT_PATH)
        with self.assertRaisesRegex(ValueError, "size must be finite and positive"):
            immediate.call(typed.text_to_brep, "A", "MandarinC", 0)


if __name__ == "__main__":
    unittest.main()
