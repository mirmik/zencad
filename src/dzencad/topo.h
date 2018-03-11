#ifndef DZENCAD_TOPO_H
#define DZENCAD_TOPO_H

#include <dzencad/base.h>

#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Edge.hxx>

#include <memory>

class DzenTransformShape;
class DzenTransform;

struct DzenShape : public DzenCadObject {
	virtual TopoDS_Shape shape() = 0;

	std::shared_ptr<DzenShape> transform(std::shared_ptr<DzenTransform> trsf);
	std::shared_ptr<DzenShape> translate(double x, double y, double z);
	
	std::shared_ptr<DzenShape> up(double z);
	std::shared_ptr<DzenShape> down(double z);
	std::shared_ptr<DzenShape> right(double x);
	std::shared_ptr<DzenShape> left(double x);
	std::shared_ptr<DzenShape> forw(double y);
	std::shared_ptr<DzenShape> back(double y);

	std::shared_ptr<DzenShape> rotateX(double a);
	std::shared_ptr<DzenShape> rotateY(double a);
	std::shared_ptr<DzenShape> rotateZ(double a);

	std::shared_ptr<DzenShape> mirrorX();
	std::shared_ptr<DzenShape> mirrorY();
	std::shared_ptr<DzenShape> mirrorZ();

	std::shared_ptr<DzenShape> mirrorXY();
	std::shared_ptr<DzenShape> mirrorYZ();
	std::shared_ptr<DzenShape> mirrorXZ();

	
	//friend std::shared_ptr<DzenShape> operator+ (const DzenShape& lhs, const DzenShape& rhs);
	//friend std::shared_ptr<DzenShape> operator- (const DzenShape& lhs, const DzenShape& rhs);
	//friend std::shared_ptr<DzenShape> operator^ (const DzenShape& lhs, const DzenShape& rhs);
};

template <typename Self>
struct DzenShapeInterface : public DzenShape {
	TopoDS_Shape shape() override { 
		Self* self = static_cast<Self*>(this);
		return self->native; 
	};

	std::shared_ptr<Self> get_spointer() {
		Self* self = static_cast<Self*>(this);
		return std::dynamic_pointer_cast<Self,DzenCadObject>(self->shared_from_this());
	}	


	std::shared_ptr<Self> transform(std::shared_ptr<DzenTransform> trsf);
	std::shared_ptr<Self> translate(double x, double y, double z);
	
	std::shared_ptr<Self> up(double z);
	std::shared_ptr<Self> down(double z);
	std::shared_ptr<Self> right(double x);
	std::shared_ptr<Self> left(double x);
	std::shared_ptr<Self> forw(double y);
	std::shared_ptr<Self> back(double y);

	std::shared_ptr<Self> rotateX(double a);
	std::shared_ptr<Self> rotateY(double a);
	std::shared_ptr<Self> rotateZ(double a);

	std::shared_ptr<Self> mirrorX();
	std::shared_ptr<Self> mirrorY();
	std::shared_ptr<Self> mirrorZ();

	std::shared_ptr<Self> mirrorXY();
	std::shared_ptr<Self> mirrorYZ();
	std::shared_ptr<Self> mirrorXZ();

};

struct DzenSolid : public DzenShapeInterface<DzenSolid> {
	TopoDS_Solid native;
};

struct DzenFace : public DzenShapeInterface<DzenFace> {
	TopoDS_Face native;
};

struct DzenEdge : public DzenShapeInterface<DzenEdge> {
	TopoDS_Edge native;
};

#endif