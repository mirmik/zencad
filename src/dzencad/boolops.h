#ifndef DZENCAD_BOOLOPS_H
#define DZENCAD_BOOLOPS_H

#include <dzencad/base.h>
#include <dzencad/topo.h>

//#include <gxx/panic.h>

#include <TopoDS.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Common.hxx>

struct DzenBooleanOperation : public DzenSolid {

};

struct DzenUnion : public DzenBooleanOperation {
	std::shared_ptr<DzenSolid> a;
	std::shared_ptr<DzenSolid> b;

	DzenUnion(std::shared_ptr<DzenSolid> a, std::shared_ptr<DzenSolid> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		TopoDS_Shape shp = BRepAlgoAPI_Fuse(a->native, b->native);
		native = TopoDS::Solid(shp);
	}
};

struct DzenDifference : public DzenBooleanOperation {
	std::shared_ptr<DzenSolid> a;
	std::shared_ptr<DzenSolid> b;

	DzenDifference(std::shared_ptr<DzenSolid> a, std::shared_ptr<DzenSolid> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		TopoDS_Shape shp = BRepAlgoAPI_Cut(a->native, b->native);
		native = TopoDS::Solid(shp);
	}
};

struct DzenIntersect : public DzenBooleanOperation {
	std::shared_ptr<DzenSolid> a;
	std::shared_ptr<DzenSolid> b;

	DzenIntersect(std::shared_ptr<DzenSolid> a, std::shared_ptr<DzenSolid> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		TopoDS_Shape shp = BRepAlgoAPI_Common(a->native, b->native);
		native = TopoDS::Solid(shp);
	}
};
/*
static inline std::shared_ptr<DzenSolid> boolops_union(std::shared_ptr<DzenSolid> a, std::shared_ptr<DzenShape> b) {
	return std::shared_ptr<DzenSolid>(new DzenUnion(a, b));
}*/

#endif