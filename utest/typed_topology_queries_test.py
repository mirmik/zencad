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
from OCP.TopAbs import TopAbs_FACE, TopAbs_VERTEX
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import (
    TopoDS_Compound,
    TopoDS_CompSolid,
    TopoDS_Edge,
    TopoDS_Face,
    TopoDS_Iterator,
    TopoDS_Shell,
    TopoDS_Solid,
    TopoDS_Vertex,
    TopoDS_Wire,
)
from OCP.gp import gp_Pnt, gp_Trsf, gp_Vec

from zencad import _typed as typed
from zencad._typed._serialization import ShapeBrepSerializer
from zencad.geom.shape import Shape as ResolvedShape
from zencad.occ_compat import as_face, as_vertex


def _compound_with_compound_and_compsolid() -> TopoDS_Compound:
    builder = BRep_Builder()
    solid = BRepPrimAPI_MakeBox(2.0, 3.0, 4.0).Solid()

    inner = TopoDS_Compound()
    builder.MakeCompound(inner)
    builder.Add(inner, solid)

    compsolid = TopoDS_CompSolid()
    builder.MakeCompSolid(compsolid)
    builder.Add(compsolid, solid)

    outer = TopoDS_Compound()
    builder.MakeCompound(outer)
    builder.Add(outer, inner)
    builder.Add(outer, compsolid)
    return outer


def _compound_of_vertices(*vertices: TopoDS_Vertex) -> TopoDS_Compound:
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    for vertex in vertices:
        builder.Add(compound, vertex)
    return compound


def _explorer_count(shape: TopoDS_Solid, kind: object) -> int:
    explorer = TopExp_Explorer(shape, kind)
    count = 0
    while explorer.More():
        count += 1
        explorer.Next()
    return count


def _direct_child_count(shape: TopoDS_Compound) -> int:
    iterator = TopoDS_Iterator(shape)
    count = 0
    while iterator.More():
        count += 1
        iterator.Next()
    return count


class TypedTopologyQueriesTest(unittest.TestCase):
    def test_all_queries_have_exact_items_across_policy_matrix(self):
        observed = set()

        for mode in (EvaluationMode.DEFERRED, EvaluationMode.IMMEDIATE):
            for cache in (False, True):
                with self.subTest(mode=mode, cache=cache):
                    context = typed.Context(
                        mode=mode,
                        cache=cache,
                        cache_store=MemoryCacheStore(),
                    )
                    box = context.call(typed.box, 2, 3, 4)
                    hierarchy = typed.Compound.from_ocp(
                        _compound_with_compound_and_compsolid(),
                        context=context,
                    )

                    # Except for vertices, these deliberately preserve legacy
                    # TopExp_Explorer occurrence semantics. In particular, a
                    # box has 24 edge occurrences rather than 12 unique edges.
                    cases = (
                        (box.vertices(), typed.Vertex, TopoDS_Vertex, 8),
                        (box.edges(), typed.Edge, TopoDS_Edge, 24),
                        (box.wires(), typed.Wire, TopoDS_Wire, 6),
                        (box.faces(), typed.Face, TopoDS_Face, 6),
                        (box.shells(), typed.Shell, TopoDS_Shell, 1),
                        (box.solids(), typed.Solid, TopoDS_Solid, 1),
                        (
                            hierarchy.compounds(),
                            typed.Compound,
                            TopoDS_Compound,
                            1,
                        ),
                        (
                            hierarchy.compsolids(),
                            typed.CompSolid,
                            TopoDS_CompSolid,
                            1,
                        ),
                    )

                    policy_types = []
                    for sequence, item_type, native_type, expected_count in cases:
                        self.assertIs(type(sequence), typed.DeferredSequence)
                        self.assertEqual(len(sequence), expected_count)
                        items = list(sequence)
                        self.assertEqual(len(items), expected_count)
                        self.assertTrue(all(type(item) is item_type for item in items))
                        self.assertIs(type(items[0].native()), native_type)
                        policy_types.append(
                            (type(sequence), tuple(type(item) for item in items))
                        )

                    observed.add(tuple(policy_types))

        self.assertEqual(len(observed), 1)

    def test_indexing_composes_graph_while_len_and_iteration_materialize(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )
        vertices = context.call(typed.box, 2).vertices()

        first = vertices[0]
        last = vertices[-1]
        out_of_range = vertices[8]
        self.assertIs(type(first), typed.Vertex)
        self.assertIs(type(last), typed.Vertex)
        self.assertIs(type(out_of_range), typed.Vertex)
        self.assertEqual(events, [])

        for invalid in (True, 0.0, "0"):
            with self.subTest(index=invalid):
                with self.assertRaisesRegex(TypeError, "indices must be integers"):
                    _ = vertices[invalid]  # type: ignore[index]
        sliced = vertices[:2]
        self.assertIs(type(sliced), typed.ShapeList)
        self.assertEqual(events, [])

        self.assertIs(type(first.native()), TopoDS_Vertex)
        self.assertTrue(events)
        self.assertIs(type(last.native()), TopoDS_Vertex)
        with self.assertRaises(IndexError):
            out_of_range.native()

        length_events = []
        length_context = typed.Context.deferred(
            cache=False,
            progress_hooks=(length_events.append,),
        )
        length_vertices = length_context.call(typed.box, 2).vertices()
        self.assertEqual(length_events, [])
        self.assertEqual(len(length_vertices), 8)
        self.assertTrue(length_events)

        iteration_events = []
        iteration_context = typed.Context.deferred(
            cache=False,
            progress_hooks=(iteration_events.append,),
        )
        iteration_vertices = iteration_context.call(typed.box, 2).vertices()
        iterator = iter(iteration_vertices)
        self.assertEqual(iteration_events, [])
        self.assertIs(type(next(iterator)), typed.Vertex)
        self.assertTrue(iteration_events)

    def test_box_vertices_are_unique_by_topology_not_explorer_occurrence(self):
        native = BRepPrimAPI_MakeBox(2.0, 3.0, 4.0).Solid()
        self.assertEqual(_explorer_count(native, TopAbs_VERTEX), 48)

        context = typed.Context.deferred(cache=False)
        vertices = typed.Solid.from_ocp(native, context=context).vertices()

        self.assertEqual(len(vertices), 8)
        points = {vertex.point().value() for vertex in vertices}
        self.assertEqual(len(points), 8)

    def test_compound_query_includes_root_and_stops_before_nested_compounds(self):
        context = typed.Context.deferred(cache=False)
        hierarchy = typed.Compound.from_ocp(
            _compound_with_compound_and_compsolid(),
            context=context,
        )

        compounds = hierarchy.compounds()

        self.assertEqual(len(compounds), 1)
        self.assertEqual(_direct_child_count(compounds[0].native()), 2)

    def test_distinct_tshapes_at_same_coordinates_are_not_merged(self):
        first = BRepBuilderAPI_MakeVertex(gp_Pnt(1, 2, 3)).Vertex()
        second = BRepBuilderAPI_MakeVertex(gp_Pnt(1, 2, 3)).Vertex()
        self.assertFalse(first.IsPartner(second))

        context = typed.Context.deferred(cache=False)
        compound = typed.Compound.from_ocp(
            _compound_of_vertices(first, second),
            context=context,
        )
        vertices = compound.vertices()

        self.assertEqual(len(vertices), 2)
        self.assertEqual(
            [vertex.point().value() for vertex in vertices],
            [(1.0, 2.0, 3.0), (1.0, 2.0, 3.0)],
        )

    def test_same_tshape_at_different_locations_is_not_merged(self):
        first = BRepBuilderAPI_MakeVertex(gp_Pnt(0, 0, 0)).Vertex()
        translation = gp_Trsf()
        translation.SetTranslation(gp_Vec(10, 0, 0))
        second = as_vertex(first.Located(TopLoc_Location(translation)))
        self.assertTrue(first.IsPartner(second))
        self.assertFalse(first.IsSame(second))

        context = typed.Context.deferred(cache=False)
        compound = typed.Compound.from_ocp(
            _compound_of_vertices(first, second),
            context=context,
        )
        vertices = compound.vertices()

        self.assertEqual(len(vertices), 2)
        self.assertEqual(
            {vertex.point().value() for vertex in vertices},
            {(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)},
        )

    def test_orientation_occurrences_share_one_topology_identity(self):
        first = BRepBuilderAPI_MakeVertex(gp_Pnt(1, 2, 3)).Vertex()
        reversed_vertex = as_vertex(first.Reversed())
        self.assertTrue(first.IsSame(reversed_vertex))
        self.assertFalse(first.IsEqual(reversed_vertex))

        context = typed.Context.deferred(cache=False)
        compound = typed.Compound.from_ocp(
            _compound_of_vertices(first, reversed_vertex),
            context=context,
        )

        self.assertEqual(len(compound.vertices()), 1)

    def test_vertex_order_uses_first_topology_traversal_occurrence(self):
        third = BRepBuilderAPI_MakeVertex(gp_Pnt(3, 0, 0)).Vertex()
        first = BRepBuilderAPI_MakeVertex(gp_Pnt(1, 0, 0)).Vertex()
        second = BRepBuilderAPI_MakeVertex(gp_Pnt(2, 0, 0)).Vertex()
        reversed_third = as_vertex(third.Reversed())
        context = typed.Context.deferred(cache=False)
        compound = typed.Compound.from_ocp(
            _compound_of_vertices(third, first, second, reversed_third),
            context=context,
        )

        self.assertEqual(
            [vertex.point().value() for vertex in compound.vertices()],
            [(3.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)],
        )

    def test_vertex_point_composes_with_a_deferred_query(self):
        events = []
        context = typed.Context.deferred(
            cache=False,
            progress_hooks=(events.append,),
        )

        point = context.call(typed.box, 2, 3, 4).vertices()[0].point()

        self.assertIs(type(point), typed.Point3)
        self.assertEqual(events, [])
        x, y, z = point.value()
        self.assertIn(x, (0.0, 2.0))
        self.assertIn(y, (0.0, 3.0))
        self.assertIn(z, (0.0, 4.0))
        self.assertTrue(events)

    def test_cached_item_hit_does_not_recompute_the_uncached_query(self):
        store = MemoryCacheStore()
        first = typed.Context.deferred(cache=True, cache_store=store)
        first.call(typed.box, 2).vertices()[0].native()

        events = []
        second = typed.Context.deferred(
            cache=True,
            cache_store=store,
            progress_hooks=(events.append,),
        )

        self.assertIs(type(second.call(typed.box, 2).vertices()[0].native()), TopoDS_Vertex)
        self.assertIn(
            EvaluationEventKind.CACHE_HIT,
            [event.kind for event in events],
        )
        self.assertEqual(
            {event.operation_id for event in events},
            {"zencad.typed.shape.vertices.item"},
        )

    def test_wrong_cached_query_item_kind_is_rejected_and_recomputed(self):
        store = MemoryCacheStore()
        first = typed.Context.deferred(cache=True, cache_store=store)
        first.call(typed.box, 2).vertices()[0].native()

        vertex_entries = [
            (key, record)
            for key, record in store.records.items()
            if record.result_type_id == "zencad.typed.Vertex.v1"
        ]
        self.assertEqual(len(vertex_entries), 1)
        key, record = vertex_entries[0]

        face_explorer = TopExp_Explorer(
            BRepPrimAPI_MakeBox(2.0, 2.0, 2.0).Solid(),
            TopAbs_FACE,
        )
        self.assertTrue(face_explorer.More())
        face = as_face(face_explorer.Current())
        wrong_value = ShapeBrepSerializer().dumps(ResolvedShape(face))
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
        restored = second.call(typed.box, 2).vertices()[0]

        self.assertIs(type(restored), typed.Vertex)
        self.assertIs(type(restored.native()), TopoDS_Vertex)
        self.assertIn(
            EvaluationEventKind.CACHE_REJECTED,
            [event.kind for event in events],
        )


if __name__ == "__main__":
    unittest.main()
