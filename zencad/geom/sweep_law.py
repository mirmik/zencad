from OCC.Core.GeomFill import GeomFill_Frenet, GeomFill_EvolvedSection, GeomFill_CorrectedFrenet, GeomFill_CurveAndTrihedron
from OCC.Core.Law import Law_Constant


class LawFunction:
    def __init__(self, law):
        self.law = law

    def Law(self):
        return self.law


class LawSection:
    def __init__(self, law):
        self.law = law

    def Law(self):
        return self.law


class LawLocation:
    def __init__(self, law):
        self.law = law

    def Law(self):
        return self.law


class LawTrihedron:
    def __init__(self, law):
        self.law = law

    def Law(self):
        return self.law


def law_constant_function(radius, range):
    aFunc = Law_Constant()
    aFunc.Set(radius, range[0], range[1])
    return LawFunction(aFunc)


def law_evolved_section(crv, lawfunc):
    return LawSection(GeomFill_EvolvedSection(crv.Curve(), lawfunc.Law()))


def law_spine_and_trihedron(crv, trilaw):
    aLoc = GeomFill_CurveAndTrihedron(trilaw.Law())
    aLoc.SetCurve(crv.HCurveAdaptor())
    return LawLocation(aLoc)


def law_corrected_frenet_trihedron():
    return LawTrihedron(GeomFill_CorrectedFrenet())


def law_frenet_trihedron():
    return LawTrihedron(GeomFill_Frenet())
