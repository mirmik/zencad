#ifndef DZENCAD_BOOLOPS_H
#define DZENCAD_BOOLOPS_H

#include <zencad/base.h>
//#include <zencad/topo.h>

#include <gxx/print.h>

#include <TopoDS.hxx>
#include <TopoDS_CompSolid.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Compound.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Common.hxx>

//#include <zencad/widget.h>

template <typename Topo>
struct ZenUnion : public Topo {
	virtual const char* class_name() const override { return "ZenUnion"; }
	std::shared_ptr<Topo> a;
	std::shared_ptr<Topo> b;

	ZenUnion(std::shared_ptr<Topo> a, std::shared_ptr<Topo> b) : a(a), b(b) {
	//	Topo::set_hash1(typeid(this).hash_code() ^ a->hash1 ^ b->hash1);
	//	Topo::set_hash2(typeid(this).hash_code() + a->hash2 + b->hash2);
	}

	void doit() override {
		a->prepare();
		b->prepare();
		Topo::m_native = BRepAlgoAPI_Fuse(a->native(), b->native());
	}
};

template <typename Topo>
struct ZenDifference : public Topo {
	virtual const char* class_name() const override { return "ZenDifference"; }
	std::shared_ptr<Topo> a;
	std::shared_ptr<Topo> b;

	ZenDifference(std::shared_ptr<Topo> a, std::shared_ptr<Topo> b) : a(a), b(b) {
	//	Topo::set_hash1(typeid(this).hash_code() ^ a->hash1 ^ b->hash1);
	//	Topo::set_hash2(typeid(this).hash_code() + a->hash2 + b->hash2);
	}

	void doit() override {
		a->prepare();
		b->prepare();
		Topo::m_native = BRepAlgoAPI_Cut(a->native(), b->native());
	}
};

template <typename Topo>
struct ZenIntersect : public Topo {
	virtual const char* class_name() const override { return "ZenIntersect"; }
	std::shared_ptr<Topo> a;
	std::shared_ptr<Topo> b;

	ZenIntersect(std::shared_ptr<Topo> a, std::shared_ptr<Topo> b) : a(a), b(b) {
	//	Topo::set_hash1(typeid(this).hash_code() ^ a->hash1 ^ b->hash1);
	//	Topo::set_hash2(typeid(this).hash_code() + a->hash2 + b->hash2);
	}

	void doit() override {
		a->prepare();
		b->prepare();
		Topo::m_native = BRepAlgoAPI_Common(a->native(), b->native());
	}
};

#endif