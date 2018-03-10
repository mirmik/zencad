#ifndef DZENCAD_TOPO_H
#define DZENCAD_TOPO_H

#include <dzencad/base.h>

#include <TopoDS_Shape.hxx>

#include <memory>

class DzenTransformShape;
class DzenTransform;

struct DzenShape : public DzenCadObject {
	TopoDS_Shape native;
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

	std::shared_ptr<DzenShape> get_spointer() const;	

	friend std::shared_ptr<DzenShape> operator+ (const DzenShape& lhs, const DzenShape& rhs);
	friend std::shared_ptr<DzenShape> operator- (const DzenShape& lhs, const DzenShape& rhs);
	friend std::shared_ptr<DzenShape> operator^ (const DzenShape& lhs, const DzenShape& rhs);
};

struct DzenSolid : public DzenShape {};

#endif