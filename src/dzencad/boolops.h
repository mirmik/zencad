#ifndef DZENCAD_BOOLOPS_H
#define DZENCAD_BOOLOPS_H

#include <dzencad/base.h>
#include <dzencad/topo.h>

#include <gxx/print.h>

#include <TopoDS.hxx>
#include <TopoDS_CompSolid.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Compound.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Common.hxx>

#include <dzencad/widget.h>

struct DzenBooleanOperation : public DzenSolid {

};

struct DzenUnion : public DzenBooleanOperation {
	virtual const char* class_name() { return "DzenUnion"; }
	std::shared_ptr<DzenSolid> a;
	std::shared_ptr<DzenSolid> b;

	DzenUnion(std::shared_ptr<DzenSolid> a, std::shared_ptr<DzenSolid> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		m_native = BRepAlgoAPI_Fuse(a->native(), b->native());
	}
};

struct DzenDifference : public DzenBooleanOperation {
	virtual const char* class_name() { return "DzenDifference"; }
	std::shared_ptr<DzenSolid> a;
	std::shared_ptr<DzenSolid> b;

	DzenDifference(std::shared_ptr<DzenSolid> a, std::shared_ptr<DzenSolid> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		m_native = BRepAlgoAPI_Cut(a->native(), b->native());
	}
};

struct DzenIntersect : public DzenBooleanOperation {
	virtual const char* class_name() { return "DzenIntersect"; }
	std::shared_ptr<DzenSolid> a;
	std::shared_ptr<DzenSolid> b;

	DzenIntersect(std::shared_ptr<DzenSolid> a, std::shared_ptr<DzenSolid> b) : a(a), b(b) {}

	void doit() override {
		a->prepare();
		b->prepare();
		m_native = BRepAlgoAPI_Common(a->native(), b->native());
	}
};
/*
static inline std::shared_ptr<DzenSolid> boolops_union(std::shared_ptr<DzenSolid> a, std::shared_ptr<DzenShape> b) {
	return std::shared_ptr<DzenSolid>(new DzenUnion(a, b));
}*/

#endif