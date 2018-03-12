#ifndef DZENCAD_SOLID_H
#define DZENCAD_SOLID_H

#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeTorus.hxx>

#include <dzencad/topo.h>
#include <memory>

#include <pybind11/pybind11.h>

namespace py = pybind11;

struct DzenBox : public DzenSolid {
	virtual const char* class_name() { return "DzenBox"; }
	double x, y, z;
	bool center = false;
	DzenBox(double x, double y, double z) : x(x), y(y), z(z) {
		set_hash1(typeid(this).hash_code() ^ make_hash(x) ^ make_hash(y) ^ make_hash(z));
		set_hash2(typeid(this).hash_code() + make_hash(x) + make_hash(y) + make_hash(z));
	}
	DzenBox(double x, double y, double z, py::kwargs kw) : DzenBox(x,y,z) {
		center = kw["center"].cast<bool>();
	}
	void doit() override { 
		if (!center) {
			m_native = BRepPrimAPI_MakeBox(x, y, z).Solid(); 
		} else {
			gp_Ax2 ax2(gp_Pnt(-x/2,-y/2,-z/2), gp_Vec(0,0,1));
			m_native = BRepPrimAPI_MakeBox(ax2, x, y, z).Solid(); 			
		}
	}
};

struct DzenSphere : public DzenSolid {
	virtual const char* class_name() { return "DzenSphere"; }
	double r;
	DzenSphere(double r) : r(r) {
		set_hash1(typeid(this).hash_code() ^ make_hash(r));
		set_hash2(typeid(this).hash_code() + make_hash(r));
	}
	void doit() override { m_native = BRepPrimAPI_MakeSphere(r).Solid(); }
};

struct DzenCylinder : public DzenSolid {
	virtual const char* class_name() { return "DzenCylinder"; }
	double r, h;
	DzenCylinder(double r, double h) : r(r), h(h) {
		set_hash1(typeid(this).hash_code() ^ make_hash(r) ^ make_hash(h));
		set_hash2(typeid(this).hash_code() + make_hash(r) + make_hash(h));}
	void doit() override { m_native = BRepPrimAPI_MakeCylinder(r, h).Solid(); }
};

struct DzenTorus : public DzenSolid {
	virtual const char* class_name() { return "DzenTorus"; }
	double r1, r2;
	DzenTorus(double r1, double r2) : r1(r1), r2(r2) {
		set_hash1(typeid(this).hash_code() ^ make_hash(r1) ^ make_hash(r2));
		set_hash2(typeid(this).hash_code() + make_hash(r1) + make_hash(r2));}
	void doit() override { m_native = BRepPrimAPI_MakeTorus(r1,r2).Solid(); }
};
/*
static inline std::shared_ptr<DzenSolid> solid_box(double x, double y, double z) {
	return std::shared_ptr<DzenSolid>(new DzenBox(x, y, z));
}

static inline std::shared_ptr<DzenSolid> solid_sphere(double r) {
	return std::shared_ptr<DzenSolid>(new DzenSphere(r));
}

static inline std::shared_ptr<DzenSolid> solid_cylinder(double r, double h) {
	return std::shared_ptr<DzenSolid>(new DzenCylinder(r, h));
}

static inline std::shared_ptr<DzenSolid> solid_torus(double r1, double r2) {
	return std::shared_ptr<DzenSolid>(new DzenTorus(r1, r2));
}*/


#endif