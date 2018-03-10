#ifndef DZENCAD_TRANSFORM_H
#define DZENCAD_TRANSFORM_H

#include <dzencad/topo.h>
#include <gp_Trsf.hxx>

#include <BRepBuilderAPI_Transform.hxx>

//#include <gxx/math/malgo3.h>

class DzenShape;

struct DzenTransform : public DzenCadObject {
	gp_Trsf trsf;
};

/*struct DzenTransformShape : public DzenShape {
	std::shared_ptr<DzenShape> shp;
	std::shared_ptr<DzenTransform> trsf;
	DzenTransformShape(	std::shared_ptr<DzenShape> shp, std::shared_ptr<DzenTransform> trsf) :
		shp(shp), trsf(trsf) {}	

	void doit() override {
		shp->prepare();
		trsf->prepare();
		BRepBuilderAPI_Transform algo(shp->shape(), trsf->trsf, true);
		native = algo.Shape();
	}
};*/

struct DzenTranslate : public DzenTransform {
	double x, y, z;
	DzenTranslate(double x, double y, double z) : x(x), y(y), z(z) {}
	void doit() override;
};

struct DzenRotation : public DzenTransform {
	//malgo::matrix3<double> mat;
	double ax, ay, az;
	double angle;
	DzenRotation(double ax, double ay, double az, double angle) : ax(ax), ay(ay), az(az), angle(angle) {}
	void doit() override;
};

struct DzenAxisMirror : public DzenTransform {
	double ax, ay, az;
	DzenAxisMirror(double ax, double ay, double az) : ax(ax), ay(ay), az(az) {}
	void doit() override;
};

struct DzenPlaneMirror : public DzenTransform {
	double ax, ay, az;
	DzenPlaneMirror(double ax, double ay, double az) : ax(ax), ay(ay), az(az) {}
	void doit() override;
};

static inline std::shared_ptr<DzenTransform> trans_translate(double x, double y, double z) {
	return std::shared_ptr<DzenTransform>(new DzenTranslate(x,y,z));
}

static inline std::shared_ptr<DzenTransform> trans_rotateX(double a) {
	return std::shared_ptr<DzenTransform>(new DzenRotation(1,0,0,a));
}

static inline std::shared_ptr<DzenTransform> trans_rotateY(double a) {
	return std::shared_ptr<DzenTransform>(new DzenRotation(0,1,0,a));
}

static inline std::shared_ptr<DzenTransform> trans_rotateZ(double a) {
	return std::shared_ptr<DzenTransform>(new DzenRotation(0,0,1,a));
}

static inline std::shared_ptr<DzenTransform> trans_mirrorX() {
	return std::shared_ptr<DzenTransform>(new DzenAxisMirror(1,0,0));
}

static inline std::shared_ptr<DzenTransform> trans_mirrorY() {
	return std::shared_ptr<DzenTransform>(new DzenAxisMirror(0,1,0));
}

static inline std::shared_ptr<DzenTransform> trans_mirrorZ() {
	return std::shared_ptr<DzenTransform>(new DzenAxisMirror(0,0,1));
}

static inline std::shared_ptr<DzenTransform> trans_mirrorXY() {
	return std::shared_ptr<DzenTransform>(new DzenPlaneMirror(0,0,1));
}

static inline std::shared_ptr<DzenTransform> trans_mirrorYZ() {
	return std::shared_ptr<DzenTransform>(new DzenPlaneMirror(1,0,0));
}

static inline std::shared_ptr<DzenTransform> trans_mirrorXZ() {
	return std::shared_ptr<DzenTransform>(new DzenPlaneMirror(0,1,0));
}

struct DzenTransformMultiply : public DzenTransform {
	std::shared_ptr<DzenTransform> a;
	std::shared_ptr<DzenTransform> b;
	DzenTransformMultiply(std::shared_ptr<DzenTransform> a, std::shared_ptr<DzenTransform> b) : a(a), b(b) {}
	void doit() override;
};

static inline std::shared_ptr<DzenTransform> trans_multiply(std::shared_ptr<DzenTransform> a, std::shared_ptr<DzenTransform> b) {
	return std::shared_ptr<DzenTransform>(new DzenTransformMultiply(a, b));
}




#endif