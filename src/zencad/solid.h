#ifndef DZENCAD_SOLID_H
#define DZENCAD_SOLID_H

#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeTorus.hxx>
//#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepPrimAPI_MakePrism.hxx>

#include <zencad/topo.h>
#include <zencad/math3.h>
#include <memory>

#include <pybind11/pybind11.h>

namespace py = pybind11;

struct ZenBox : public ZenSolid {
	virtual const char* class_name() { return "ZenBox"; }
	double x, y, z;
	bool center = false;
	ZenBox(double x, double y, double z) : x(x), y(y), z(z) {
		set_hash1(typeid(this).hash_code() ^ make_hash(x) ^ make_hash(y) ^ make_hash(z));
		set_hash2(typeid(this).hash_code() + make_hash(x) + make_hash(y) + make_hash(z));
	}
	ZenBox(double x, double y, double z, py::kwargs kw) : ZenBox(x,y,z) {
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

struct ZenSphere : public ZenSolid {
	virtual const char* class_name() { return "ZenSphere"; }
	double r;
	ZenSphere(double r) : r(r) {
		set_hash1(typeid(this).hash_code() ^ make_hash(r));
		set_hash2(typeid(this).hash_code() + make_hash(r));
	}
	void doit() override { m_native = BRepPrimAPI_MakeSphere(r).Solid(); }
};

struct ZenCylinder : public ZenSolid {
	virtual const char* class_name() { return "ZenCylinder"; }
	double r, h;
	ZenCylinder(double r, double h) : r(r), h(h) {
		set_hash1(typeid(this).hash_code() ^ make_hash(r) ^ make_hash(h));
		set_hash2(typeid(this).hash_code() + make_hash(r) + make_hash(h));}
	void doit() override { m_native = BRepPrimAPI_MakeCylinder(r, h).Solid(); }
};

struct ZenTorus : public ZenSolid {
	virtual const char* class_name() { return "ZenTorus"; }
	double r1, r2;
	ZenTorus(double r1, double r2) : r1(r1), r2(r2) {
		set_hash1(typeid(this).hash_code() ^ make_hash(r1) ^ make_hash(r2));
		set_hash2(typeid(this).hash_code() + make_hash(r1) + make_hash(r2));}
	void doit() override { m_native = BRepPrimAPI_MakeTorus(r1,r2).Solid(); }
};

struct ZenLinearExtrude : public ZenSolid {
	virtual const char* class_name() { return "ZenLinearExtrude"; }
	gp_Vec vec;
	std::shared_ptr<ZenFace> fc;
	ZenLinearExtrude(std::shared_ptr<ZenFace> fc, double z) : fc(fc), vec(0,0,z) {}
	ZenLinearExtrude(std::shared_ptr<ZenFace> fc, ZenVector3 v) : fc(fc), vec(v.Vec()) {}
	void doit() override { 
		BRepPrimAPI_MakePrism mk(fc->native(), vec);
		m_native = mk; 
	}
};

#endif