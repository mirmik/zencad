#ifndef DZENCAD_TOPO_H
#define DZENCAD_TOPO_H

#include <dzencad/base.h>

#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Edge.hxx>

#include <dzencad/trans.h>
#include <gxx/print.h>

#include <memory>

class DzenTransformShape;
class DzenTransform;

struct DzenShape : public DzenCadObject {
	const TopoDS_Shape& native() {
		if (!prepared) {
			gxx::println("DzenCadError: object isn't prepared");
			exit(-1);
		}
		return m_native;
	}

	//virtual TopoDS_Shape shape() = 0;

	//std::shared_ptr<DzenShape> transform(std::shared_ptr<DzenTransform> trsf);
	//std::shared_ptr<DzenShape> translate(double x, double y, double z);
	//
	//std::shared_ptr<DzenShape> up(double z);
	//std::shared_ptr<DzenShape> down(double z);
	//std::shared_ptr<DzenShape> right(double x);
	//std::shared_ptr<DzenShape> left(double x);
	//std::shared_ptr<DzenShape> forw(double y);
	//std::shared_ptr<DzenShape> back(double y);
//
	//std::shared_ptr<DzenShape> rotateX(double a);
	//std::shared_ptr<DzenShape> rotateY(double a);
	//std::shared_ptr<DzenShape> rotateZ(double a);
//
	//std::shared_ptr<DzenShape> mirrorX();
	//std::shared_ptr<DzenShape> mirrorY();
	//std::shared_ptr<DzenShape> mirrorZ();
//
	//std::shared_ptr<DzenShape> mirrorXY();
	//std::shared_ptr<DzenShape> mirrorYZ();
	//std::shared_ptr<DzenShape> mirrorXZ();

protected:
	TopoDS_Shape m_native;
};

template <typename Self>
struct DzenShapeInterface : public DzenShape {
	//TopoDS_Shape shape() override { 
	//	Self* self = static_cast<Self*>(this);
	//	return self->native; 
	//};

	std::shared_ptr<Self> get_spointer() const {
		Self* self = static_cast<Self*>( const_cast<DzenShapeInterface*>(this) );
		return std::dynamic_pointer_cast<Self,DzenCadObject>(self->shared_from_this());
	}	

	std::shared_ptr<Self> transform(std::shared_ptr<DzenTransform> trsf) {
		return std::shared_ptr<Self>(new DzenTransformed<Self>(get_spointer(), trsf));
	}

	std::shared_ptr<Self> translate(double x, double y, double z) {
		return transform(std::shared_ptr<DzenTransform>(new DzenTranslate(x, y, z)));
	}
	
	std::shared_ptr<Self> right	(double x) 	{ return translate(  x,  0,  0); }
	std::shared_ptr<Self> left	(double x) 	{ return translate( -x,  0,  0); }
	std::shared_ptr<Self> forw	(double y) 	{ return translate(  0,  y,  0); }
	std::shared_ptr<Self> back	(double y) 	{ return translate(  0, -y,  0); }
	std::shared_ptr<Self> up	(double z)	{ return translate(  0,  0,  z); }
	std::shared_ptr<Self> down	(double z) 	{ return translate(  0,  0, -z); }
	
	std::shared_ptr<Self> rotateX(double a) { return transform(trans_rotateX(a)); }
	std::shared_ptr<Self> rotateY(double a) { return transform(trans_rotateY(a)); }
	std::shared_ptr<Self> rotateZ(double a) { return transform(trans_rotateZ(a)); }

	std::shared_ptr<Self> mirrorX() { return transform(trans_mirrorX()); }
	std::shared_ptr<Self> mirrorY() { return transform(trans_mirrorY()); }
	std::shared_ptr<Self> mirrorZ() { return transform(trans_mirrorZ()); }

	std::shared_ptr<Self> mirrorXY() { return transform(trans_mirrorXY()); }
	std::shared_ptr<Self> mirrorYZ() { return transform(trans_mirrorYZ()); }
	std::shared_ptr<Self> mirrorXZ() { return transform(trans_mirrorXZ()); }
};


struct DzenSolid : public DzenShapeInterface<DzenSolid> {
	//TopoDS_Solid native;
	//TopoDS_Shape shape() {
	// 	gxx::println("shape");
	// 	return native; 
	//}
	//TopoDS_Solid to_native(const TopoDS_Shape& shp) { return TopoDS::Solid(shp); } 

	friend std::shared_ptr<DzenSolid> operator+ (const DzenSolid& lhs, const DzenSolid& rhs);
	friend std::shared_ptr<DzenSolid> operator- (const DzenSolid& lhs, const DzenSolid& rhs);
	friend std::shared_ptr<DzenSolid> operator^ (const DzenSolid& lhs, const DzenSolid& rhs);

	std::shared_ptr<DzenSolid> get_spointer() const;
};

struct DzenFace : public DzenShapeInterface<DzenFace> {
	//TopoDS_Shape shape() { return native; }
	//TopoDS_Face native;
};

struct DzenEdge : public DzenShapeInterface<DzenEdge> {
	//TopoDS_Shape shape() { return native; }
	//TopoDS_Edge native;
};

#endif