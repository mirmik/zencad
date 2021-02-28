from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common


def occ_pair_union(a, b):
    algo = BRepAlgoAPI_Fuse(a, b)
    algo.Build()
    if not algo.IsDone():
        raise Exception("warn: union algotithm failed\n")
    return algo.Shape()


def occ_pair_difference(a, b):
    algo = BRepAlgoAPI_Cut(a, b)
    algo.Build()
    if not algo.IsDone():
        raise Exception("warn: difference algotithm failed\n")
    return algo.Shape()


def occ_pair_intersect(a, b):
    algo = BRepAlgoAPI_Common(a, b)
    algo.Build()
    if not algo.IsDone():
        raise Exception("warn: intersect algotithm failed\n")
    return algo.Shape()
