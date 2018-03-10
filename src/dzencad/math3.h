#ifndef DZENCAD_MATH_H
#define DZENCAD_MATH_H

struct XYZ {
	double x, y, z;
	XYZ(double x, double y, double z) : x(x), y(y), z(z) {}
};

struct DzenDirection3 : public XYZ {
	DzenDirection3(double x, double y, double z) : XYZ(x,y,z) {}
};

struct DzenVector3 : public XYZ {
	DzenVector3(double x, double y, double z) : XYZ(x,y,z) {}
};

struct DzenPoint3 : public XYZ {
	DzenPoint3(double x, double y, double z) : XYZ(x,y,z) {}
	gp_Pnt Pnt() { return gp_Pnt(x,y,z); }
};

#endif