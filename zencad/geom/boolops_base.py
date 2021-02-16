from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common


def occ_pair_union(a, b):
    algo = BRepAlgoAPI_Fuse(a, b)
    algo.Build()
    if not algo.IsDone():
        print("warn: union algotithm failed\n")
        algo.GetReport().Dump(sys.stdout)
    return algo.Shape()


def occ_pair_difference(a, b):
    algo = BRepAlgoAPI_Cut(a, b)
    algo.Build()
    if not algo.IsDone():
        print("warn: union algotithm failed\n")
        algo.GetReport().Dump(sys.stdout)
    return algo.Shape()


def occ_pair_intersect(a, b):
    algo = BRepAlgoAPI_Common(a, b)
    algo.Build()
    if not algo.IsDone():
        print("warn: union algotithm failed\n")
        algo.GetReport().Dump(sys.stdout)
    return algo.Shape()
