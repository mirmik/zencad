#ifndef DZENCAD_FACE_H
#define DZENCAD_FACE_H

#include <zencad/topo.h>
#include <memory>

#include <pybind11/pybind11.h>
#include <BRepBuilderAPI_MakeFace.hxx>

struct ZenWireFace : public ZenFace {
	std::shared_ptr<ZenWire> wr;
	ZenWireFace(std::shared_ptr<ZenWire> wr) : wr(wr) {}
	void doit() {
		wr->prepare();
		BRepBuilderAPI_MakeFace alg(wr->native);
		m_native = alg.Face();
	}
};

#endif