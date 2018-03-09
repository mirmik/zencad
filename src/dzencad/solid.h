#ifndef DZENCAD_SOLID_H
#define DZENCAD_SOLID_H

#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>

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

static inline std::shared_ptr<DzenShape> solid_box(double x, double y, double z) {
	return std::shared_ptr<DzenShape>(new DzenBox(x,y,z));
}

static inline std::shared_ptr<DzenShape> solid_sphere(double r) {
	return std::shared_ptr<DzenShape>(new DzenSphere(r));
}


#endif