from zencad.shape import Shape, nocached_shape_generator, shape_generator
from zencad.lazy import *
from OCC.Core.TopAbs import TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_FACE, TopAbs_SOLID, TopAbs_SHELL, TopAbs_COMPOUND, TopAbs_COMPSOLID
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_Sewing
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Solid
from OCC.Core.TopExp import TopExp_Explorer

def _unify_faces_array(input):
	ret = []
	fset = {}

	for i in input:
		surface = breptool.Surface(i)

		adaptor_surface = BRepAdaptor_Surface(i.Face())
		surface_type = adaptor_surface.GetType()

		if surface_type == GeomAbs_Plane:
			pln = Handle(Geom_Plane).DownCast(surface)
			pln0 = pln.Pln()

			found = False

			for key, arr in fset.items():
				pnt = key.D0(0, 0);
				pln1 = key.Pln();

				dir0 = pln0.Axis().Direction();
				dir1 = pln1.Axis().Direction();

				if (dir0.IsEqual(dir1, 0.00001) and
				    abs(pln0.Distance(pln1.Axis().Location())) < 0.0000001 and
				    abs(pln1.Distance(pln0.Axis().Location())) < 0.0000001):

					found = True
					arr.append(i)
					break;

			if found == False:
				fset.append((pln, [i]))

		else:
			ret.append(i)
			continue;

	for key, arr in fset.items():
		farr = _make_union(pr.second)
		ret.emplace_back(_unify_face(farr))

	return ret;

def _unify_shell(proto):
	faces = []
	mkShell = BRepOffsetAPI_Sewing()

	newfaces = _unify_faces_array(proto.faces())
	for n in newfaces:
		mkShell.Add(n.Shape());

	mkShell.Perform();
	return mkShell.SewedShape()


def _unify_solid(proto):
	mkSolid = BRepBuilderAPI_MakeSolid()
	explorer = TopExp_Explorer()

	explorer.Init(proto.Shape(), TopAbs_SHELL)
	while explorer.More():
		mkSolid.Add(_unify_shell(Shape(explorer.Current())).Shell())
		explorer.Next()

	mkSolid.Build()
	return mkSolid.Shape();

def _unify_compound(proto):
	builder = BRep_Builder()
	comp = TopoDS_Compound()

	builder.MakeCompound(comp);

	explorer = TopExp_Explorer()

	explorer.Init(proto.Shape(), TopAbs_SOLID)
	while explorer.More():
		builder.Add(comp, _unify_solid(Shape(explorer.Current())).Solid())
		explorer.Next()

	explorer.Init(proto.Shape(), TopAbs_SHELL, TopAbs_SOLID)
	while explorer.More():
		builder.Add(comp, _unify_shell(Shape(explorer.Current())).Shell())
		explorer.Next()

	faces = []
	explorer.Init(proto.Shape(), TopAbs_FACE, TopAbs_SHELL)
	while explorer.More():
		faces.append(Shape(explorer.Current()))
		explorer.Next()

	faces_new = _unify_faces_array(faces)
	for f in faces_new:
		builder.Add(comp, f.Shape())

	return comp
	

@lazy.lazy(cls=shape_generator)
def unify(proto):
	_Shape = proto.Shape()

	if _Shape.IsNull(): raise Exception("Cannot remove splitter from empty shape");
	elif _Shape.ShapeType() == TopAbs_SOLID: return _unify_solid(proto)
	elif _Shape.ShapeType() == TopAbs_SHELL: return _unify_shell(proto)
	elif _Shape.ShapeType() == TopAbs_FACE:	return _unify_face(proto)
	elif _Shape.ShapeType() == TopAbs_COMPOUND: return _unify_compound(proto)
	
	raise Exception("TODO");