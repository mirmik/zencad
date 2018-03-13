#ifndef DZENCAD_MATH_H
#define DZENCAD_MATH_H

#include <gp_Pnt.hxx>

struct XYZ {
	double x, y, z;
	XYZ(double x, double y, double z) : x(x), y(y), z(z) {}
};

struct ZenDirection3 : public XYZ {
	ZenDirection3(double x, double y, double z) : XYZ(x,y,z) {}
};

struct ZenVector3 : public XYZ {
	ZenVector3(double x, double y, double z) : XYZ(x,y,z) {}
};

struct ZenPoint3 : public XYZ {
	ZenPoint3(double x, double y, double z) : XYZ(x,y,z) {}
	gp_Pnt Pnt() { return gp_Pnt(x,y,z); }
};

#endif