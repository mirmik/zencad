#ifndef DZENCAD_FACE_H
#define DZENCAD_FACE_H

#include <zencad/topo.h>
#include <zencad/vertex.h>
#include <memory>
#include <vector>
#include <set>
#include <pybind11/pybind11.h>

namespace py = pybind11;

struct ZenFilletFace;

struct ZenFace : public ZenShape, public ZenShapeTransI<ZenFace>, public ZenBoolOpsI<ZenFace> {
	const char* class_name() { return "ZenFace"; }

	std::shared_ptr<ZenFace> spointer() const {
		ZenFace* self = const_cast<ZenFace*>(this);
		return std::dynamic_pointer_cast<ZenFace,ZenCadObject>(self->shared_from_this());
	}
	std::shared_ptr<ZenFilletFace> fillet(double rad, py::list nums);
};
/*
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
*/
struct ZenPolygon : public ZenFace {
	const char* class_name() const override { return "ZenPolygon"; }
	std::vector<ZenPoint3> pnts;
	ZenPolygon(pybind11::list args);
	void doit() override;
	void vreflect(ZenVisitor& v) override;
};

struct ZenCircle : public ZenFace {
	const char* class_name() const override { return "ZenCircle"; }
	double r;
	ZenCircle(double r);
	void doit() override;
	void vreflect(ZenVisitor& v) override;
};

struct ZenFilletFace : public ZenFace {
	const char* class_name() const override { return "ZenFilletFace"; }
	double r;
	std::shared_ptr<ZenFace> fc;
	std::set<int> nums;
	ZenFilletFace(std::shared_ptr<ZenFace> fc, std::set<int> nums, double r);
	void doit() override;
	void vreflect(ZenVisitor& v) override;
};

#endif