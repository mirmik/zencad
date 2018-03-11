#ifndef DZENCAD_WIRE_H
#define DZENCAD_WIRE_H

#include <dzencad/topo.h>
//#include <dzencad/face.h>
#include <dzencad/math3.h>
#include <memory>

#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>

#include <pybind11/pybind11.h>

/*class DzenWireUnion : public DzenWire {
	std::shared_ptr<DzenWire> a;
	std::shared_ptr<DzenWire> b;

	DzenWireUnion(std::shared_ptr<DzenWire> a, std::shared_ptr<DzenWire> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		native = BRepAlgoAPI_Fuse(a->native, b->native);
	}
};
}*/

class DzenFace;

struct DzenWire : public DzenShapeInterface<DzenWire> {
	TopoDS_Wire native;
	std::shared_ptr<DzenFace> make_face();
};

struct DzenSegment : public DzenEdge {
	DzenPoint3 a; 
	DzenPoint3 b;

	DzenSegment(DzenPoint3 a, DzenPoint3 b) : a(a), b(b) {}
	void doit() override { 
		native = BRepBuilderAPI_MakeEdge(a.Pnt(), b.Pnt()); 
	}
};

struct DzenPolySegment : public DzenWire {
	std::vector<DzenPoint3> pnts;
	bool closed;
	
	DzenPolySegment(pybind11::list args) {
    	for (auto item : args)
          	pnts.push_back(item.cast<DzenPoint3>());
	}

	DzenPolySegment(pybind11::list args, pybind11::kwargs kw) : DzenPolySegment(args) {
        closed = kw["closed"].cast<bool>();
	}


	void doit() override { 
		BRepBuilderAPI_MakeWire mkWire;
		for (int i = 0; i < pnts.size() - 1; ++i) {
			mkWire.Add(BRepBuilderAPI_MakeEdge(pnts[i].Pnt(), pnts[i+1].Pnt()));
		}
		if (closed) mkWire.Add(BRepBuilderAPI_MakeEdge(pnts[pnts.size()-1].Pnt(), pnts[0].Pnt()));
		native = mkWire.Wire(); 
	}
};


#endif