#include <zencad/solid.h>
#include <zencad/face.h>
#include <zencad/wire.h>

#include <gp_Circ.hxx>
#include <TopExp_Explorer.hxx>
#include <TopAbs.hxx>

#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepFilletAPI_MakeFillet2d.hxx>
#include <BRepTools_WireExplorer.hxx>
//#include <BRepTools_FaceExplorer.hxx>

#include <Geom_Circle.hxx>
#include <GC_MakeCircle.hxx>

const char* makeFaceErrorToStr(const auto& err) {
	switch(err) {
		case BRepBuilderAPI_FaceDone: return "BRepBuilderAPI_FaceDone";
		case BRepBuilderAPI_NoFace: return "BRepBuilderAPI_NoFace";
		case BRepBuilderAPI_NotPlanar: return "BRepBuilderAPI_NotPlanar";
		case BRepBuilderAPI_CurveProjectionFailed: return "BRepBuilderAPI_CurveProjectionFailed";
		case BRepBuilderAPI_ParametersOutOfRange: return "BRepBuilderAPI_ParametersOutOfRange";
		default: return "UndefinedError";
	};
}

void ZenWireFace::doit() {
	wr->prepare();
	BRepBuilderAPI_MakeFace alg(TopoDS::Wire(wr->native()));

	auto sts = alg.Error();
	if (sts != BRepBuilderAPI_FaceDone) 
		gxx::println(makeFaceErrorToStr(sts));
	
	m_native = alg.Face();
}

void ZenEdgeFace::doit() {
	wr->prepare();
	BRepBuilderAPI_MakeFace alg(wr->wire());

	auto sts = alg.Error();
	if (sts != BRepBuilderAPI_FaceDone) 
		gxx::println(makeFaceErrorToStr(sts));
	
	m_native = alg.Face();
}

void ZenCircle::doit() {
	gp_Circ EL ( gp::XOY(), r );
	Handle(Geom_Circle) anCircle = GC_MakeCircle(EL).Value();
	TopoDS_Edge aEdge = BRepBuilderAPI_MakeEdge( anCircle );
	TopoDS_Wire aCircle = BRepBuilderAPI_MakeWire( aEdge );
	m_native = BRepBuilderAPI_MakeFace(aCircle);
}

void ZenPolygon::doit() {
	BRepBuilderAPI_MakePolygon mk;
	for (auto& p : pnts) mk.Add(p.Pnt());
	mk.Close();
	m_native = BRepBuilderAPI_MakeFace(mk);
}

std::shared_ptr<ZenFilletFace> ZenFace::fillet(int num) {
	return std::shared_ptr<ZenFilletFace>(new ZenFilletFace(get_spointer(), num));
};

void ZenFilletFace::doit() {
	BRepFilletAPI_MakeFillet2d mk(TopoDS::Face(fc->native()));
	for(TopExp_Explorer expWire(TopoDS::Face(fc->native()), TopAbs_WIRE); expWire.More(); expWire.Next()) {
		BRepTools_WireExplorer explorer(TopoDS::Wire(expWire.Current()));
    	while (explorer.More()) {
			mk.AddFillet(explorer.CurrentVertex(), r);
			explorer.Next();
		}
	}
	m_native = mk;
}