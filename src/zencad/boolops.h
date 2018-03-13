#ifndef DZENCAD_BOOLOPS_H
#define DZENCAD_BOOLOPS_H

#include <zencad/base.h>
#include <zencad/topo.h>

#include <gxx/print.h>

#include <TopoDS.hxx>
#include <TopoDS_CompSolid.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Compound.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Common.hxx>

#include <zencad/widget.h>

struct ZenBooleanOperation : public ZenSolid {

};

struct ZenUnion : public ZenBooleanOperation {
	virtual const char* class_name() override { return "ZenUnion"; }
	std::shared_ptr<ZenSolid> a;
	std::shared_ptr<ZenSolid> b;

	ZenUnion(std::shared_ptr<ZenSolid> a, std::shared_ptr<ZenSolid> b) : a(a), b(b) {
		set_hash1(typeid(this).hash_code() ^ a->hash1 ^ b->hash1);
		set_hash2(typeid(this).hash_code() + a->hash2 + b->hash2);
	}

	void doit() override {
		a->prepare();
		b->prepare();
		m_native = BRepAlgoAPI_Fuse(a->native(), b->native());
	}
};

struct ZenDifference : public ZenBooleanOperation {
	virtual const char* class_name() override { return "ZenDifference"; }
	std::shared_ptr<ZenSolid> a;
	std::shared_ptr<ZenSolid> b;

	ZenDifference(std::shared_ptr<ZenSolid> a, std::shared_ptr<ZenSolid> b) : a(a), b(b) {
		set_hash1(typeid(this).hash_code() ^ a->hash1 ^ b->hash1);
		set_hash2(typeid(this).hash_code() + a->hash2 + b->hash2);
	}

	void doit() override {
		a->prepare();
		b->prepare();
		m_native = BRepAlgoAPI_Cut(a->native(), b->native());
	}
};

struct ZenIntersect : public ZenBooleanOperation {
	virtual const char* class_name() override { return "ZenIntersect"; }
	std::shared_ptr<ZenSolid> a;
	std::shared_ptr<ZenSolid> b;

	ZenIntersect(std::shared_ptr<ZenSolid> a, std::shared_ptr<ZenSolid> b) : a(a), b(b) {
		set_hash1(typeid(this).hash_code() ^ a->hash1 ^ b->hash1);
		set_hash2(typeid(this).hash_code() + a->hash2 + b->hash2);
	}

	void doit() override {
		a->prepare();
		b->prepare();
		m_native = BRepAlgoAPI_Common(a->native(), b->native());
	}
};
/*
static inline std::shared_ptr<ZenSolid> boolops_union(std::shared_ptr<ZenSolid> a, std::shared_ptr<ZenShape> b) {
	return std::shared_ptr<ZenSolid>(new ZenUnion(a, b));
}*/

#endif