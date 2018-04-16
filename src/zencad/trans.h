#ifndef DZENCAD_TRANSFORM_H
#define DZENCAD_TRANSFORM_H

#include <zencad/base.h>
#include <gp_Trsf.hxx>
#include <BRepBuilderAPI_Transform.hxx>

class ZenShape;

struct ZenTransform : public ZenCadObject {
	gp_Trsf trsf;
	void dump(std::ostream& out) override { out.write((char*)&trsf, sizeof(gp_Trsf)); }
	void load(std::istream& out) override { out.read((char*)&trsf, sizeof(gp_Trsf)); }
	const char* class_name() const override { return "ZenTransform"; }
};

template<typename Topo>
struct ZenTransformed : public Topo {
	std::shared_ptr<ZenTransform> trsf;
	std::shared_ptr<Topo> topo;
	ZenTransformed(std::shared_ptr<Topo> topo, std::shared_ptr<ZenTransform> trsf) : trsf(trsf), topo(topo) { Topo::initialize_hash(); }
	
	void doit() override {
		topo->prepare();
		trsf->prepare();
		BRepBuilderAPI_Transform algo(topo->native(), trsf->trsf, true);
		Topo::m_native = algo.Shape();
	}

	const char* class_name() const override { return "ZenTransformed"; }
	void vreflect(ZenVisitor& v) override { v & *trsf; v & *topo; }

	
};

struct ZenTranslate : public ZenTransform {
	const char* class_name() const override { return "ZenTranslate"; }
	double x, y, z;
	ZenTranslate(double x, double y, double z) : x(x), y(y), z(z) {	initialize_hash();
		gxx::fprintln("ZenTranslate {},{},{},{}",x,y,z,hash);
	}
	void doit() override;
	void vreflect(ZenVisitor& v) override { v & x; v & y; v & z; }
};

struct ZenRotate : public ZenTransform {
	const char* class_name() const override { return "ZenRotate"; }
	double ax, ay, az;
	double angle;
	ZenRotate(double ax, double ay, double az, double angle) : ax(ax), ay(ay), az(az), angle(angle) { initialize_hash(); }
	void doit() override;
	void vreflect(ZenVisitor& v) override { v & ax; v & ay; v & az; v & angle; }
};

struct ZenAxisMirror : public ZenTransform {
	const char* class_name() const override { return "ZenAxisMirror"; }
	double ax, ay, az;
	ZenAxisMirror(double ax, double ay, double az) : ax(ax), ay(ay), az(az) { initialize_hash(); }
	void doit() override;
	void vreflect(ZenVisitor& v) override { v & ax; v & ay; v & az; }
};

struct ZenPlaneMirror : public ZenTransform {
	const char* class_name() const override { return "ZenPlaneMirror"; }
	double ax, ay, az;
	ZenPlaneMirror(double ax, double ay, double az) : ax(ax), ay(ay), az(az) { initialize_hash(); }
	void doit() override;
	void vreflect(ZenVisitor& v) override { v & ax; v & ay; v & az; }
};

static inline std::shared_ptr<ZenTransform> trans_translate(double x, double y, double z) {
	return std::shared_ptr<ZenTransform>(new ZenTranslate(x,y,z));
}

static inline std::shared_ptr<ZenTransform> trans_rotateX(double a) {
	return std::shared_ptr<ZenTransform>(new ZenRotate(1,0,0,a));
}

static inline std::shared_ptr<ZenTransform> trans_rotateY(double a) {
	return std::shared_ptr<ZenTransform>(new ZenRotate(0,1,0,a));
}

static inline std::shared_ptr<ZenTransform> trans_rotateZ(double a) {
	return std::shared_ptr<ZenTransform>(new ZenRotate(0,0,1,a));
}

static inline std::shared_ptr<ZenTransform> trans_mirrorX() {
	return std::shared_ptr<ZenTransform>(new ZenAxisMirror(1,0,0));
}

static inline std::shared_ptr<ZenTransform> trans_mirrorY() {
	return std::shared_ptr<ZenTransform>(new ZenAxisMirror(0,1,0));
}

static inline std::shared_ptr<ZenTransform> trans_mirrorZ() {
	return std::shared_ptr<ZenTransform>(new ZenAxisMirror(0,0,1));
}

static inline std::shared_ptr<ZenTransform> trans_mirrorXY() {
	return std::shared_ptr<ZenTransform>(new ZenPlaneMirror(0,0,1));
}

static inline std::shared_ptr<ZenTransform> trans_mirrorYZ() {
	return std::shared_ptr<ZenTransform>(new ZenPlaneMirror(1,0,0));
}

static inline std::shared_ptr<ZenTransform> trans_mirrorXZ() {
	return std::shared_ptr<ZenTransform>(new ZenPlaneMirror(0,1,0));
}
/*
struct ZenTransformMultiply : public ZenTransform {
	std::shared_ptr<ZenTransform> a;
	std::shared_ptr<ZenTransform> b;
	ZenTransformMultiply(std::shared_ptr<ZenTransform> a, std::shared_ptr<ZenTransform> b) : a(a), b(b) { initialize_hash(); }
	void doit() override;
};

static inline std::shared_ptr<ZenTransform> trans_multiply(std::shared_ptr<ZenTransform> a, std::shared_ptr<ZenTransform> b) {
	return std::shared_ptr<ZenTransform>(new ZenTransformMultiply(a, b));
}*/

#endif