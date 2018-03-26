#ifndef DZENCAD_SOLID_H
#define DZENCAD_SOLID_H

#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeTorus.hxx>
//#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRepPrimAPI_MakeWedge.hxx>
#include <BRepOffsetAPI_ThruSections.hxx>
#include <BRepOffsetAPI_MakePipe.hxx>

#include <zencad/topo.h>
#include <zencad/math3.h>
#include <memory>

#include <pybind11/pybind11.h>

namespace py = pybind11;

struct ZenBox : public ZenSolid {
	const char* class_name() const override { return "ZenBox"; }
	double x, y, z;
	bool center = false;
	ZenBox(double x, double y, double z) : x(x), y(y), z(z) {
		initialize_hash();
	}
	
	ZenBox(double x, double y, double z, py::kwargs kw) : ZenBox(x,y,z) {
		center = kw["center"].cast<bool>();
		initialize_hash();
	}
	
	void doit() override { 
		if (!center) {
			m_native = BRepPrimAPI_MakeBox(x, y, z).Solid(); 
		} else {
			gp_Ax2 ax2(gp_Pnt(-x/2,-y/2,-z/2), gp_Vec(0,0,1));
			m_native = BRepPrimAPI_MakeBox(ax2, x, y, z).Solid(); 			
		}
	}

	void vreflect(ZenVisitor& v) {
		v & x; v & y; v & z; v & center;
	}
};

struct ZenSphere : public ZenSolid {
	const char* class_name() const override { return "ZenSphere"; }
	double r;
	ZenSphere(double r) : r(r) {
		//set_hash1(typeid(this).hash_code() ^ make_hash(r));
		//set_hash2(typeid(this).hash_code() + make_hash(r));
	}
	void doit() override { m_native = BRepPrimAPI_MakeSphere(r).Solid(); }
};

struct ZenCylinder : public ZenSolid {
	const char* class_name() const override { return "ZenCylinder"; }
	double r, h;
	ZenCylinder(double r, double h) : r(r), h(h) { }
		//set_hash1(typeid(this).hash_code() ^ make_hash(r) ^ make_hash(h));
		//set_hash2(typeid(this).hash_code() + make_hash(r) + make_hash(h));}
	void doit() override { m_native = BRepPrimAPI_MakeCylinder(r, h).Solid(); }
};

struct ZenTorus : public ZenSolid {
	const char* class_name() const override { return "ZenTorus"; }
	double r1, r2;
	ZenTorus(double r1, double r2) : r1(r1), r2(r2) {}
		//set_hash1(typeid(this).hash_code() ^ make_hash(r1) ^ make_hash(r2));
		//set_hash2(typeid(this).hash_code() + make_hash(r1) + make_hash(r2));}
	void doit() override { m_native = BRepPrimAPI_MakeTorus(r1,r2).Solid(); }
};

struct ZenWedge : public ZenSolid {
	const char* class_name() const override { return "ZenWedge"; }
	double x, y, z, ltx;
	ZenWedge(double x, double y, double z, double ltx) : x(x), y(y), z(z), ltx(ltx) {}
		//set_hash1(typeid(this).hash_code() ^ make_hash(x) ^ make_hash(y) ^ make_hash(z) ^ make_hash(ltx));
		//set_hash2(typeid(this).hash_code() + make_hash(x) + make_hash(y) + make_hash(z) + make_hash(ltx));}
	void doit() override { m_native = BRepPrimAPI_MakeWedge(x,y,z,ltx).Solid(); }
};

struct ZenLinearExtrude : public ZenSolid {
	const char* class_name() const override { return "ZenLinearExtrude"; }
	gp_Vec vec;
	std::shared_ptr<ZenFace> fc;
	ZenLinearExtrude(std::shared_ptr<ZenFace> fc, double z) : fc(fc), vec(0,0,z) {}
	ZenLinearExtrude(std::shared_ptr<ZenFace> fc, ZenVector3 v) : fc(fc), vec(v.Vec()) {}
	void doit() override;
};


struct ZenLoft : public ZenSolid {
	const char* class_name() const override { return "ZenLoft"; }
	std::vector<std::shared_ptr<ZenShape>> shapes;

	ZenLoft(pybind11::list args) {
    	for (auto item : args) {
    		auto pnt = item.cast<std::shared_ptr<ZenShape>>();
    		shapes.push_back(pnt);
    	}
	}

	void doit() override;
};


struct ZenPipe : public ZenSolid {
	const char* class_name() const override { return "ZenPipe"; }
	std::shared_ptr<ZenWire> path;
	std::shared_ptr<ZenShape> profile;

	ZenPipe(std::shared_ptr<ZenWire> path, std::shared_ptr<ZenShape> profile) 
		: profile(profile), path(path) 
	{
    	
	}

	void doit() override;
};

#endif