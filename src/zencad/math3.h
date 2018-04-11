#ifndef DZENCAD_MATH_H
#define DZENCAD_MATH_H

#include <gp_Pnt.hxx>
#include <BRepBuilderAPI_MakeVertex.hxx>
#include <gxx/print.h>

#include <zencad/base.h>

struct XYZ {
	double x, y, z;
	XYZ(const XYZ& oth) : x(oth.x), y(oth.y), z(oth.z) {}
	XYZ(double x, double y, double z) : x(x), y(y), z(z) {}
	size_t printTo(gxx::io::ostream& o) const {
		return gxx::fprint_to(o,"[{},{},{}]", x, y, z);
	};
};
/*
struct ZenDirection3 : public XYZ {
	ZenDirection3(double x, double y, double z) : XYZ(x,y,z) {}
};

struct ZenVector3 : public XYZ {
	ZenVector3(double x, double y, double z) : XYZ(x,y,z) {}
	gp_Vec Vec() { return gp_Vec(x,y,z); }	
};*/

#endif