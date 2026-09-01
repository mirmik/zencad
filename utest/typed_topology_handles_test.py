from typing import get_type_hints
import unittest

from evalcache.v2 import (
    CacheRecord,
    EvaluationEventKind,
    EvaluationMode,
    MemoryCacheStore,
)
from OCP.BRep import BRep_Builder
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.TopAbs import (
    TopAbs_EDGE,
    TopAbs_FACE,
    TopAbs_SHELL,
    TopAbs_VERTEX,
    TopAbs_WIRE,
)
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import (
    TopoDS_CompSolid,
    TopoDS_Compound,
    TopoDS_Edge,
    TopoDS_Face,
    TopoDS_Iterator,
    TopoDS_Shape,
    TopoDS_Shell,
    TopoDS_Solid,
    TopoDS_Vertex,
    TopoDS_Wire,
)
from OCP.gp import gp_Pnt

from zencad import _typed as typed
from zencad._typed._serialization import ShapeBrepSerializer
from zencad.geom.shape import Shape as ResolvedShape
from zencad.occ_compat import as_edge, as_face, as_shell, as_vertex, as_wire


def _first_subshape(shape, kind, convert):
    explorer = TopExp_Explorer(shape, kind)
    if not explorer.More():
        raise AssertionError(f"test fixture has no {kind!r}")
    return convert(explorer.Current())


def _topology_samples():
    solid = BRepPrimAPI_MakeBox(2.0, 3.0, 4.0).Solid()
    shell = _first_subshape(solid, TopAbs_SHELL, as_shell)
    face = _first_subshape(solid, TopAbs_FACE, as_face)
    wire = _first_subshape(solid, TopAbs_WIRE, as_wire)
    edge = _first_subshape(solid, TopAbs_EDGE, as_edge)
    vertex = _first_subshape(solid, TopAbs_VERTEX, as_vertex)

    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    builder.Add(compound, solid)

    compsolid = TopoDS_CompSolid()
    builder.MakeCompSolid(compsolid)
    builder.Add(compsolid, solid)

    return (
        (typed.Vertex, TopoDS_Vertex, vertex),
        (typed.Edge, TopoDS_Edge, edge),
        (typed.Wire, TopoDS_Wire, wire),
        (typed.Face, TopoDS_Face, face),
        (typed.Shell, TopoDS_Shell, shell),
        (typed.Solid, TopoDS_Solid, solid),
        (typed.Compound, TopoDS_Compound, compound),
        (typed.CompSolid, TopoDS_CompSolid, compsolid),
    )


def _direct_child_count(shape):
    iterator = TopoDS_Iterator(shape)
    count = 0
    while iterator.More():
        count += 1
        iterator.Next()
    return count


class TypedTopologyHandlesTest(unittest.TestCase):
    def test_all_topology_handles_have_exact_native_boundaries(self):
        context = typed.Context.deferred(cache=False)

        for handle_type, native_type, source in _topology_samples():
            with self.subTest(handle=handle_type.__name__):
                self.assertEqual(handle_type.__bases__, (typed.Shape,))
                self.assertIs(get_type_hints(handle_type.native)["return"], native_type)

                handle = handle_type.from_ocp(source, context=context)
                self.assertIs(type(handle), handle_type)
                first = handle.native()
                second = handle.native()
                self.assertIs(type(first), native_type)
                self.assertIs(type(second), native_type)
                self.assertIsNot(first, second)
                self.assertFalse(first.IsNull())
                self.assertFalse(second.IsNull())

                source.Nullify()
                first.Nullify()
                self.assertFalse(handle.native().IsNull())
                self.assertFalse(second.IsNull())

    def test_transform_and_translate_preserve_each_topology_handle(self):
        context = typed.Context.deferred(cache=False)
        transform = context.call(typed.translation, -2, 5, 7) * context.call(typed.scale, -1.5)

        for handle_type, native_type, source in _topology_samples():
            with self.subTest(handle=handle_type.__name__):
                handle = handle_type.from_ocp(source, context=context)
                translated = handle.translate(1, 2, 3)
                transformed = handle.transform(transform)

                self.assertIs(type(translated), handle_type)
                self.assertIs(type(transformed), handle_type)
                self.assertIs(type(translated.native()), native_type)
                self.assertIs(type(transformed.native()), native_type)
                self.assertEqual(
                    translated.native().ShapeType(),
                    source.ShapeType(),
                )
                self.assertEqual(
                    transformed.native().ShapeType(),
                    source.ShapeType(),
                )

    def test_box_and_vertex_point_are_policy_independent(self):
        observed_types = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    solid = context.call(typed.box, 1, 2, 3)
                    moved = solid.translate(4, 5, 6)
                    vertex = typed.Vertex.from_ocp(
                        BRepBuilderAPI_MakeVertex(gp_Pnt(1.25, -2.5, 4.75)).Vertex(),
                        context=context,
                    )
                    point = vertex.point()
                    topology_handles = tuple(
                        handle_type.from_ocp(source, context=context)
                        for handle_type, _, source in _topology_samples()
                    )
                    translated_handles = tuple(
                        handle.translate(1, 2, 3) for handle in topology_handles
                    )

                    observed_types.add(
                        (
                            type(solid),
                            type(moved),
                            type(vertex),
                            type(point),
                            tuple(type(handle) for handle in topology_handles),
                            tuple(type(handle) for handle in translated_handles),
                        )
                    )
                    self.assertIs(type(solid), typed.Solid)
                    self.assertIs(type(moved), typed.Solid)
                    self.assertIs(type(vertex), typed.Vertex)
                    self.assertIs(type(point), typed.Point3)
                    self.assertEqual(point.value(), (1.25, -2.5, 4.75))
                    self.assertIs(type(solid.native()), TopoDS_Solid)
                    for (handle_type, native_type, _), handle in zip(
                        _topology_samples(), translated_handles
                    ):
                        self.assertIs(type(handle), handle_type)
                        self.assertIs(type(handle.native()), native_type)

        self.assertEqual(len(observed_types), 1)

    def test_from_ocp_validates_topology_kind_and_null_shapes(self):
        context = typed.Context.deferred(cache=False)
        samples = _topology_samples()

        for index, (handle_type, _, _) in enumerate(samples):
            wrong_source = samples[(index + 1) % len(samples)][2]
            with self.subTest(handle=handle_type.__name__):
                with self.assertRaises(TypeError):
                    handle_type.from_ocp(wrong_source, context=context)

        with self.assertRaises(ValueError):
            typed.Shape.from_ocp(TopoDS_Shape(), context=context)
        with self.assertRaises(ValueError):
            typed.Vertex.from_ocp(TopoDS_Vertex(), context=context)
        with self.assertRaises(TypeError):
            typed.Vertex.from_ocp(gp_Pnt(), context=context)

    def test_from_ocp_and_native_are_deep_snapshots(self):
        context = typed.Context.deferred(cache=False)
        source = _topology_samples()[-2][2]
        self.assertIs(type(source), TopoDS_Compound)
        handle = typed.Compound.from_ocp(source, context=context)
        self.assertEqual(_direct_child_count(source), 1)

        builder = BRep_Builder()
        builder.Add(source, BRepPrimAPI_MakeBox(1.0, 1.0, 1.0).Solid())
        self.assertEqual(_direct_child_count(source), 2)
        # The deferred import owns bytes captured before the source mutation.
        self.assertEqual(_direct_child_count(handle.native()), 1)

        exported = handle.native()
        builder.Add(exported, BRepPrimAPI_MakeBox(1.0, 1.0, 1.0).Solid())
        self.assertEqual(_direct_child_count(exported), 2)
        self.assertEqual(_direct_child_count(handle.native()), 1)

    def test_wrong_cached_topology_kind_is_rejected_and_recomputed(self):
        store = MemoryCacheStore()
        first = typed.Context.deferred(cache=True, cache_store=store)
        first.call(typed.box, 2).native()

        key, record = next(iter(store.records.items()))
        native_face = _topology_samples()[3][2]
        wrong_value = ShapeBrepSerializer().dumps(ResolvedShape(native_face))
        store.records[key] = CacheRecord(
            schema=record.schema,
            result_type_id=record.result_type_id,
            serializer_id=record.serializer_id,
            value=wrong_value,
        )

        events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )
        restored = second.call(typed.box, 2)

        self.assertIs(type(restored), typed.Solid)
        self.assertIs(type(restored.native()), TopoDS_Solid)
        self.assertIn(
            EvaluationEventKind.CACHE_REJECTED,
            [event.kind for event in events],
        )

    def test_booleans_return_general_shape(self):
        context = typed.Context.deferred(cache=False)
        outer = context.call(typed.box, 3)
        inner = context.call(typed.box, 2).translate(0.5, 0.5, 0.5)

        result = outer - inner

        self.assertIs(type(result), typed.Shape)
        self.assertIs(type(result.native()), TopoDS_Shape)
        self.assertFalse(result.native().IsNull())


if __name__ == "__main__":
    unittest.main()
