#ifndef ZENCAD_VERTEX_H
#define ZENCAD_VERTEX_H

#include <gp_Pnt.hxx>
#include <BRepBuilderAPI_MakeVertex.hxx>

#include <gxx/print.h>

#include <zencad/base.h>

struct ZenVertex : public ZenShape, public ZenShapeTransI<ZenVertex> {
	const char* class_name() const { return "ZenVertex"; }

	std::shared_ptr<ZenVertex> spointer() const {
		ZenVertex* self = const_cast<ZenVertex*>(this);
		return std::dynamic_pointer_cast<ZenVertex,ZenCadObject>(self->shared_from_this());
	}
};

struct ZenPoint3 : public ZenVertex {
	double x, y, z;
	
	const char* class_name() const override { return "ZenPoint3"; }
	ZenPoint3(double x, double y) : x(x), y(y), z(0) { initialize_hash(); }
	ZenPoint3(double x, double y, double z) : x(x), y(y), z(z) { initialize_hash(); }
	gp_Pnt Pnt() { return gp_Pnt(x,y,z); }
	void vreflect(ZenVisitor& v) override { v&x; v&y; v&z; }

	void prepare() override {
		m_native = BRepBuilderAPI_MakeVertex(Pnt()).Vertex();
	};

	size_t printTo(gxx::io::ostream& o) const {	return gxx::fprint_to(o, "({},{},{})", x, y, z); }
};

#endif