#ifndef DZENCAD_BOOLOPS_H
#define DZENCAD_BOOLOPS_H

#include <dzencad/base.h>
#include <dzencad/topo.h>

//#include <gxx/panic.h>

#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Common.hxx>

struct DzenBooleanOperation : public DzenShape {

};

struct DzenUnion : public DzenBooleanOperation {
	std::shared_ptr<DzenShape> a;
	std::shared_ptr<DzenShape> b;

	DzenUnion(std::shared_ptr<DzenShape> a, std::shared_ptr<DzenShape> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		native = BRepAlgoAPI_Fuse(a->native, b->native);
	}
};

struct DzenDifference : public DzenBooleanOperation {
	std::shared_ptr<DzenShape> a;
	std::shared_ptr<DzenShape> b;

	DzenDifference(std::shared_ptr<DzenShape> a, std::shared_ptr<DzenShape> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		native = BRepAlgoAPI_Cut(a->native, b->native);
	}
};

struct DzenIntersect : public DzenBooleanOperation {
	std::shared_ptr<DzenShape> a;
	std::shared_ptr<DzenShape> b;

	DzenIntersect(std::shared_ptr<DzenShape> a, std::shared_ptr<DzenShape> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		native = BRepAlgoAPI_Common(a->native, b->native);
	}
};

static inline std::shared_ptr<DzenShape> boolops_union(std::shared_ptr<DzenShape> a, std::shared_ptr<DzenShape> b) {
	return std::shared_ptr<DzenShape>(new DzenUnion(a, b));
}

#endif