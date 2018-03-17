#ifndef DZENCAD_MATH_H
#define DZENCAD_MATH_H

#include <gp_Pnt.hxx>
#include <gxx/print.h>

struct XYZ {
	double x, y, z;
	XYZ(double x, double y, double z) : x(x), y(y), z(z) {}
	size_t printTo(gxx::io::ostream& o) const {
		return gxx::fprint_to(o,"[{},{},{}]", x, y, z);
	};
};

struct ZenDirection3 : public XYZ {
	ZenDirection3(double x, double y, double z) : XYZ(x,y,z) {}
};

struct ZenVector3 : public XYZ {
	ZenVector3(double x, double y, double z) : XYZ(x,y,z) {}
	gp_Vec Vec() { return gp_Vec(x,y,z); }	
};

struct ZenPoint3 : public XYZ {
	ZenPoint3(double x, double y) : XYZ(x,y,0) {}
	ZenPoint3(double x, double y, double z) : XYZ(x,y,z) {}
	gp_Pnt Pnt() { return gp_Pnt(x,y,z); }
};

#endif