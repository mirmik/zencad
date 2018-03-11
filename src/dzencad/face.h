#ifndef DZENCAD_FACE_H
#define DZENCAD_FACE_H

#include <dzencad/topo.h>
#include <memory>

#include <pybind11/pybind11.h>
#include <BRepBuilderAPI_MakeFace.hxx>

struct DzenWireFace : public DzenFace {
	std::shared_ptr<DzenWire> wr;
	DzenWireFace(std::shared_ptr<DzenWire> wr) : wr(wr) {}
	void doit() {
		wr->prepare();
		BRepBuilderAPI_MakeFace alg(wr->native);
		native = alg.Face();
	}
};

#endif