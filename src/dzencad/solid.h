#ifndef DZENCAD_SOLID_H
#define DZENCAD_SOLID_H

#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeTorus.hxx>

#include <dzencad/topo.h>
#include <memory>

struct DzenBox : public DzenShape {
	double x, y, z;
	DzenBox(double x, double y, double z) : x(x), y(y), z(z) {}
	void doit() override { native = BRepPrimAPI_MakeBox(x, y, z).Shape(); }
};

struct DzenSphere : public DzenShape {
	double r;
	DzenSphere(double r) : r(r) {}
	void doit() override { native = BRepPrimAPI_MakeSphere(r).Shape(); }
};

struct DzenCylinder : public DzenShape {
	double r, h;
	DzenCylinder(double r, double h) : r(r), h(h) {}
	void doit() override { native = BRepPrimAPI_MakeCylinder(r, h).Shape(); }
};

struct DzenTorus : public DzenShape {
	double r1, r2;
	DzenTorus(double r1, double r2) : r1(r1), r2(r2) {}
	void doit() override { native = BRepPrimAPI_MakeTorus(r1,r2).Shape(); }
};

static inline std::shared_ptr<DzenShape> solid_box(double x, double y, double z) {
	return std::shared_ptr<DzenShape>(new DzenBox(x, y, z));
}

static inline std::shared_ptr<DzenShape> solid_sphere(double r) {
	return std::shared_ptr<DzenShape>(new DzenSphere(r));
}

static inline std::shared_ptr<DzenShape> solid_cylinder(double r, double h) {
	return std::shared_ptr<DzenShape>(new DzenCylinder(r, h));
}

static inline std::shared_ptr<DzenShape> solid_torus(double r1, double r2) {
	return std::shared_ptr<DzenShape>(new DzenTorus(r1, r2));
}


#endif