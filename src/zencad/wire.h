#ifndef DZENCAD_WIRE_H
#define DZENCAD_WIRE_H

#include <gp_Circ.hxx>

#include <zencad/topo.h>
//#include <zencad/face.h>
#include <zencad/math3.h>
#include <memory>

#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <GC_MakeArcOfCircle.hxx>
#include <TopAbs.hxx>

#include <pybind11/pybind11.h>

/*class ZenWireUnion : public ZenWire {
	std::shared_ptr<ZenWire> a;
	std::shared_ptr<ZenWire> b;

	ZenWireUnion(std::shared_ptr<ZenWire> a, std::shared_ptr<ZenWire> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		native = BRepAlgoAPI_Fuse(a->native, b->native);
	}
};
}*/
/*
class ZenFace;

struct ZenWire : public ZenShapeInterface<ZenWire> {
	using native_type = TopoDS_Wire;
	static constexpr TopAbs_ShapeEnum shape_topabs = TopAbs_WIRE;
	static native_type shape_convert(const TopoDS_Shape& shp) { return TopoDS::Wire(shp); }

	const char* class_name() const override { return "ZenWire"; }
	TopoDS_Shape shape() { return m_native; }
	std::shared_ptr<ZenFace> make_face();
};

struct ZenEdge : public ZenShapeInterface<ZenEdge> {
	using native_type = TopoDS_Edge;
	static constexpr TopAbs_ShapeEnum shape_topabs = TopAbs_EDGE;
	static native_type shape_convert(const TopoDS_Shape& shp) { return TopoDS::Edge(shp); }

	const char* class_name() { return "ZenEdge"; }
	std::shared_ptr<ZenFace> make_face();
	TopoDS_Wire wire() { return BRepBuilderAPI_MakeWire(TopoDS::Edge(native())); }
};

struct ZenSegment : public ZenWire {
	const char* class_name() const override { return "ZenSegment"; }
	ZenPoint3 a; 
	ZenPoint3 b;

	ZenSegment(ZenPoint3 a, ZenPoint3 b) : a(a), b(b) {}
	void doit() override { 
		m_native = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(a.Pnt(), b.Pnt())); 
	}
};

struct ZenCircleArcByPoints : public ZenWire {
	const char* class_name() const override { return "ZenCircleArcByPoints"; }
	ZenPoint3  a;
	ZenPoint3  b;
	ZenPoint3  c;

	ZenCircleArcByPoints(ZenPoint3 a, ZenPoint3 b, ZenPoint3 c) : a(a), b(b), c(c) {}
	void doit() override {  
		gxx::println(a,b,c);
		m_native = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(a.Pnt(), b.Pnt(), c.Pnt())));
	}
};

struct ZenPolySegment : public ZenWire {
	const char* class_name() const override { return "ZenPolySegment"; }
	std::vector<ZenPoint3> pnts;
	bool closed;
	
	ZenPolySegment(pybind11::list args) {
    	for (auto item : args) {
    		auto pnt = item.cast<ZenPoint3>();
    		pnts.push_back(pnt);
    	}
	}

	ZenPolySegment(pybind11::list args, pybind11::kwargs kw) : ZenPolySegment(args) {
        closed = kw["closed"].cast<bool>();
	}

	void doit() override { 
		BRepBuilderAPI_MakeWire mkWire;
		for (int i = 0; i < pnts.size() - 1; ++i) {
			mkWire.Add(BRepBuilderAPI_MakeEdge(pnts[i].Pnt(), pnts[i+1].Pnt()));
		}
		if (closed) mkWire.Add(BRepBuilderAPI_MakeEdge(pnts[pnts.size()-1].Pnt(), pnts[0].Pnt()));
		m_native = mkWire.Wire(); 
	}
};

struct ZenWireCircle : public ZenWire {
	const char* class_name() const override { return "ZenWireCircle"; }
	double r; 
	bool is_arc;
	std::pair<double, double> arc;
	ZenWireCircle(double r, pybind11::kwargs kw) : r(r) {
		try {
			arc = kw["arc"].cast<std::pair<double, double>>();
			is_arc = true;
		} catch(...) {
			is_arc = false;
		}
	}
	void doit() override { 
		if (is_arc) {
			m_native = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(gp_Pnt(0,0,0), gp_Vec(0,0,1)), r), arc.first, arc.second)); 
		} else {
			m_native = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(gp_Pnt(0,0,0), gp_Vec(0,0,1)), r))); 
		}
	}
};

struct ZenWireComplex : public ZenWire {
	const char* class_name() const override { return "ZenWireComplex"; }
	
	std::vector<std::shared_ptr<ZenWire>> v;

	ZenWireComplex(pybind11::list lst) {
    	for (auto item : lst) {
    		auto wr = item.cast<std::shared_ptr<ZenWire>>();
    		v.push_back(wr);
    	}
	}
	void doit() override { 
		BRepBuilderAPI_MakeWire mkWire;
		for (int i = 0; i < v.size(); ++i) {
			mkWire.Add(TopoDS::Wire(v[i]->native()));
		}
		m_native = mkWire.Wire(); 
	}
};*/
#endif