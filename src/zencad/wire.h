#ifndef DZENCAD_WIRE_H
#define DZENCAD_WIRE_H

#include <gxx/print/stdprint.h>

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
#include <TColgp_HArray1OfPnt.hxx>
#include <TColgp_Array1OfVec.hxx>
#include <TColStd_HArray1OfBoolean.hxx>
#include <TColStd_HArray1OfReal.hxx>

#include <GeomAPI_Interpolate.hxx>

namespace py = pybind11;

struct ZenWire : public ZenShape, public ZenShapeTransI<ZenWire>, public ZenBoolOpsI<ZenWire> {
	const char* class_name() const { return "ZenSolid"; }

	std::shared_ptr<ZenWire> spointer() const {
		ZenWire* self = const_cast<ZenWire*>(this);
		return std::dynamic_pointer_cast<ZenWire,ZenCadObject>(self->shared_from_this());
	}
};


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
*/
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

	ZenCircleArcByPoints(ZenPoint3 a, ZenPoint3 b, ZenPoint3 c) : a(a), b(b), c(c) {
    	initialize_hash();
    }
	void doit() override {  
		m_native = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(a.Pnt(), b.Pnt(), c.Pnt())));
	}
};

struct ZenPolySegment : public ZenWire {
	const char* class_name() const override { return "ZenPolySegment"; }
	std::vector<ZenPoint3> pnts;
	bool closed;
	
	ZenPolySegment(pybind11::list args, bool closed) : closed(closed) {
    	for (auto item : args) {
    		auto pnt = item.cast<ZenPoint3>();
    		pnts.push_back(pnt);
    	}
    	initialize_hash();
	}

	void doit() override { 
		BRepBuilderAPI_MakeWire mkWire;
		for (int i = 0; i < pnts.size() - 1; ++i) {
			mkWire.Add(BRepBuilderAPI_MakeEdge(pnts[i].Pnt(), pnts[i+1].Pnt()));
		}
		if (closed) mkWire.Add(BRepBuilderAPI_MakeEdge(pnts[pnts.size()-1].Pnt(), pnts[0].Pnt()));
		m_native = mkWire.Wire(); 
	}

	void vreflect(ZenVisitor& v) { 
		for (auto& pnt : pnts) v&pnt; 
		v&closed;
	}
};

struct ZenWireCircle : public ZenWire {
	const char* class_name() const override { return "ZenWireCircle"; }
	double r; 
	double a;
	double b;
	
	ZenWireCircle(double r, double a, double b) : r(r), a(a), b(b) {
		initialize_hash();
	}

	void doit() override { 
		if (a==0 && b == 360) {
			m_native = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(gp_Pnt(0,0,0), gp_Vec(0,0,1)), r))); 
		} else {
			m_native = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(gp_Pnt(0,0,0), gp_Vec(0,0,1)), r), a, b)); 
		}
	}

	void vreflect(ZenVisitor& v) { v&a; v&b; v&r; }
};

struct ZenInterpolateWire : public ZenWire {
	const char* class_name() const override { return "ZenInterpolateWire"; }
	std::vector<ZenPoint3> pnts;
	std::vector<ZenVector3> tang;
	//std::vector<double> params;
	//std::vector<bool> btang;
	bool closed;
	
	ZenInterpolateWire(py::list pntslst, py::list tanglst, py::list paramslst, bool closed) : closed(closed) {
		for (auto& a : pntslst) { pnts.push_back(a.cast<ZenPoint3>()); }
		for (auto& a : tanglst) { tang.push_back(a.cast<ZenVector3>()); }
		/*if (paramslst.size()) {
			for (auto& a : paramslst) { 
				params.push_back(a.cast<double>()); 
			}
		} else { 
			for (int i = 0; i < pnts.size(); ++i) {
				params.push_back(0.1);
			} 
		}*/
		//for (auto& a : tang) { ); }
		initialize_hash();
	}

	void doit() override { 
		Handle(TColgp_HArray1OfPnt) _pnts = new TColgp_HArray1OfPnt(1, pnts.size());
		for (int i = 0; i < pnts.size(); ++i) _pnts->SetValue(i + 1, pnts[i].Pnt());

		/*Handle(TColStd_HArray1OfReal) _params = new TColStd_HArray1OfReal(1, pnts.size());
		for (int i = 0; i < pnts.size(); ++i) _params->SetValue(i + 1, params[i]);*/

		GeomAPI_Interpolate algo(_pnts, /*_params,*/ closed, 0.0000001);
		
		if (tang.size()) {
			TColgp_Array1OfVec _tang(1, tang.size());
			Handle(TColStd_HArray1OfBoolean) _bools = new TColStd_HArray1OfBoolean(1, tang.size());
			for (int i = 0; i < pnts.size(); ++i) _tang.SetValue(i + 1, tang[i].Vec());
			for (int i = 0; i < pnts.size(); ++i) _bools->SetValue(i + 1, tang[i] != ZenVector3(0,0,0));
			algo.Load(_tang, _bools);
		}
		
		algo.Perform();
		m_native = BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(algo.Curve()));
	}

	void vreflect(ZenVisitor& v) { 
		for (auto& tan : tang) v&tan; 
		for (auto& pnt : pnts) v&pnt; 
		//for (auto& param : params) v&param; 
		v&closed;
	}
};


struct ZenHelix : public ZenWire {
	const char* class_name() const override { return "ZenHelix"; }
	double r; 
	double h;
	double step;
	
	ZenHelix(double r, double h, double step) : r(r), h(h), step(step) {
		initialize_hash();
	}

	void doit() override { 
	}

	void vreflect(ZenVisitor& v) { v&r; v&h; v&step; }
};














/*
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