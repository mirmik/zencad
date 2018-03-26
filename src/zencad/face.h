#ifndef DZENCAD_FACE_H
#define DZENCAD_FACE_H

#include <zencad/topo.h>
#include <memory>
#include <pybind11/pybind11.h>

struct ZenFilletFace;

struct ZenFace : public ZenBooleanShapeInterface<ZenFace> {
	const char* class_name() { return "ZenFace"; }
	std::shared_ptr<ZenFilletFace> fillet(int num);
};

struct ZenWireFace : public ZenFace {
	const char* class_name() const override { return "ZenWireFace"; }
	std::shared_ptr<ZenWire> wr;
	ZenWireFace(std::shared_ptr<ZenWire> wr) : wr(wr) {}
	void doit() override;
};

struct ZenEdgeFace : public ZenFace {
	const char* class_name() const override { return "ZenEdgeFace"; }
	
	std::shared_ptr<ZenEdge> wr;
	ZenEdgeFace(std::shared_ptr<ZenEdge> wr) : wr(wr) {}
	void doit() override;
};

struct ZenPolygon : public ZenFace {
	const char* class_name() const override { return "ZenPolygon"; }
	
	std::vector<ZenPoint3> pnts;

	ZenPolygon(pybind11::list args) {
    	for (auto item : args) {
    		auto pnt = item.cast<ZenPoint3>();
    		pnts.push_back(pnt);
    	}
	}
	void doit() override;
};

struct ZenCircle : public ZenFace {
	const char* class_name() const override { return "ZenCircle"; }
	double r;
	ZenCircle(double r) : r(r) {}
	void doit() override;
};

struct ZenFilletFace : public ZenFace {
	double r;
	std::shared_ptr<ZenFace> fc;
	const char* class_name() { return "ZenFilletFace"; }
	ZenFilletFace(std::shared_ptr<ZenFace> fc, double r) : fc(fc), r(r) {}
	void doit() override;
};

#endif