#ifndef DZENCAD_TRANSFORM_H
#define DZENCAD_TRANSFORM_H

#include <zencad/base.h>
#include <gp_Trsf.hxx>

#include <BRepBuilderAPI_Transform.hxx>

//#include <gxx/math/malgo3.h>

class ZenShape;

struct ZenTransform : public ZenCadObject {
	gp_Trsf trsf;

	void serialize_to_stream(std::ostream& out) override {
		out.write((char*)&trsf, sizeof(gp_Trsf));
	}

	void deserialize_from_stream(std::istream& out) override {
		out.read((char*)&trsf, sizeof(gp_Trsf));
	}

	const char* class_name() override { return "ZenTransform"; }
};

template<typename Topo>
struct ZenTransformed : public Topo {
	std::shared_ptr<ZenTransform> trsf;
	std::shared_ptr<Topo> topo;
	ZenTransformed(std::shared_ptr<Topo> topo, std::shared_ptr<ZenTransform> trsf)
		: trsf(trsf), topo(topo) 
	{
		Topo::set_hash1(typeid(this).hash_code() ^ trsf->hash1 ^ topo->hash1);
		Topo::set_hash2(typeid(this).hash_code() + trsf->hash2 + topo->hash2);
	}
	
	void doit() override {
		topo->prepare();
		trsf->prepare();
		BRepBuilderAPI_Transform algo(topo->native(), trsf->trsf, true);
		Topo::m_native = algo.Shape();
	}

	const char* class_name() override { return "ZenTransformed"; }
};

struct ZenTranslate : public ZenTransform {
	const char* class_name() override { return "ZenTranslate"; }
	double x, y, z;
	ZenTranslate(double x, double y, double z) : x(x), y(y), z(z) {
		set_hash1(typeid(this).hash_code() ^ make_hash(x) ^ make_hash(y) ^ make_hash(z));
		set_hash2(typeid(this).hash_code() + make_hash(x) + make_hash(y) + make_hash(z));
	}
	void doit() override;
};

struct ZenRotate : public ZenTransform {
	const char* class_name() override { return "ZenRotate"; }
	//malgo::matrix3<double> mat;
	double ax, ay, az;
	double angle;
	ZenRotate(double ax, double ay, double az, double angle) : ax(ax), ay(ay), az(az), angle(angle) {
		set_hash1(typeid(this).hash_code() ^ make_hash(ax) ^ make_hash(ay) ^ make_hash(az) ^ make_hash(angle));
		set_hash2(typeid(this).hash_code() + make_hash(ax) + make_hash(ay) + make_hash(az) + make_hash(angle));
	}
	void doit() override;
};

struct ZenAxisMirror : public ZenTransform {
	const char* class_name() override { return "ZenAxisMirror"; }
	double ax, ay, az;
	ZenAxisMirror(double ax, double ay, double az) : ax(ax), ay(ay), az(az) {
		set_hash1(typeid(this).hash_code() ^ make_hash(ax) ^ make_hash(ay) ^ make_hash(az) );
		set_hash2(typeid(this).hash_code() + make_hash(ax) + make_hash(ay) + make_hash(az));
	}
	void doit() override;
};

struct ZenPlaneMirror : public ZenTransform {
	const char* class_name() override { return "ZenPlaneMirror"; }
	double ax, ay, az;
	ZenPlaneMirror(double ax, double ay, double az) : ax(ax), ay(ay), az(az) {
		set_hash1(typeid(this).hash_code() ^ make_hash(ax) ^ make_hash(ay) ^ make_hash(az));
		set_hash2(typeid(this).hash_code() + make_hash(ax) + make_hash(ay) + make_hash(az));
	}
	void doit() override;
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

struct ZenTransformMultiply : public ZenTransform {
	std::shared_ptr<ZenTransform> a;
	std::shared_ptr<ZenTransform> b;
	ZenTransformMultiply(std::shared_ptr<ZenTransform> a, std::shared_ptr<ZenTransform> b) : a(a), b(b) {
		set_hash1(typeid(this).hash_code() ^ a->hash1 ^ b->hash1);
		set_hash2(typeid(this).hash_code() + a->hash2 + b->hash2);
	}
	void doit() override;
};

static inline std::shared_ptr<ZenTransform> trans_multiply(std::shared_ptr<ZenTransform> a, std::shared_ptr<ZenTransform> b) {
	return std::shared_ptr<ZenTransform>(new ZenTransformMultiply(a, b));
}




#endif