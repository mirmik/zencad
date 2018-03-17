#ifndef DZENCAD_FACE_H
#define DZENCAD_FACE_H

#include <zencad/topo.h>
#include <memory>

#include <pybind11/pybind11.h>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
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
	

struct ZenWireFace : public ZenFace {
	const char* class_name() override { return "ZenWireFace"; }
	
	std::shared_ptr<ZenWire> wr;
	ZenWireFace(std::shared_ptr<ZenWire> wr) : wr(wr) {}
	void doit() {
		wr->prepare();
		BRepBuilderAPI_MakeFace alg(TopoDS::Wire(wr->native()));

		auto sts = alg.Error();
		if (sts != BRepBuilderAPI_FaceDone) 
			gxx::println(makeFaceErrorToStr(sts));
		
		m_native = alg.Face();
	}
};

struct ZenEdgeFace : public ZenFace {
	const char* class_name() override { return "ZenEdgeFace"; }
	
	std::shared_ptr<ZenEdge> wr;
	ZenEdgeFace(std::shared_ptr<ZenEdge> wr) : wr(wr) {}
	void doit() {
		wr->prepare();
		BRepBuilderAPI_MakeFace alg(wr->wire());

		auto sts = alg.Error();
		if (sts != BRepBuilderAPI_FaceDone) 
			gxx::println(makeFaceErrorToStr(sts));
		
		m_native = alg.Face();
	}
};

struct ZenPolygon : public ZenFace {
	const char* class_name() override { return "ZenPolygon"; }
	
	std::vector<ZenPoint3> pnts;

	ZenPolygon(pybind11::list args) {
    	for (auto item : args) {
    		auto pnt = item.cast<ZenPoint3>();
    		pnts.push_back(pnt);
    	}
	}

	void doit() {
		BRepBuilderAPI_MakePolygon mk;
		for (auto& p : pnts) mk.Add(p.Pnt());
		mk.Close();
		m_native = BRepBuilderAPI_MakeFace(mk);
	}
};

struct ZenCircle : public ZenFace {
	const char* class_name() override { return "ZenCircle"; }
	double r;
	ZenCircle(double r) : r(r) {}
	void doit() {
		gp_Circ EL ( gp::XOY(), r );
		Handle(Geom_Circle) anCircle = GC_MakeCircle(EL).Value();
		TopoDS_Edge aEdge = BRepBuilderAPI_MakeEdge( anCircle );
		TopoDS_Wire aCircle = BRepBuilderAPI_MakeWire( aEdge );
		m_native = BRepBuilderAPI_MakeFace(aCircle);
	}
};

#endif