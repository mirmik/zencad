#include <zencad/topo.h>
#include <zencad/trans.h>
#include <zencad/boolops.h>
#include <gxx/print.h>

/*std::shared_ptr<ZenShape> ZenShape::transform(std::shared_ptr<ZenTransform> trsf) {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trsf));
}

std::shared_ptr<ZenShape> ZenShape::translate(double x, double y, double z) {
	return transform(std::shared_ptr<ZenTransform>(new ZenTranslate(x, y, z)));
}

std::shared_ptr<ZenShape> ZenShape::up(double z) {
	return translate(0,0,z);
}

std::shared_ptr<ZenShape> ZenShape::down(double z) {
	return translate(0,0,-z);
}

std::shared_ptr<ZenShape> ZenShape::right(double x) {
	return translate(x,0,0);
}

std::shared_ptr<ZenShape> ZenShape::left(double x) {
	return translate(-x,0,0);
}

std::shared_ptr<ZenShape> ZenShape::forw(double y) {
	return translate(0,y,0);
}

std::shared_ptr<ZenShape> ZenShape::back(double y) {
	return translate(0,-y,0);
}


std::shared_ptr<ZenShape> ZenShape::rotateX(double a) {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_rotateX(a)));
}

std::shared_ptr<ZenShape> ZenShape::rotateY(double a) {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_rotateY(a)));
}

std::shared_ptr<ZenShape> ZenShape::rotateZ(double a) {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_rotateZ(a)));
}

std::shared_ptr<ZenShape> ZenShape::mirrorX() {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_mirrorX()));
}

std::shared_ptr<ZenShape> ZenShape::mirrorY() {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_mirrorY()));
}

std::shared_ptr<ZenShape> ZenShape::mirrorZ() {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_mirrorZ()));
}

std::shared_ptr<ZenShape> ZenShape::mirrorXY() {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_mirrorXY()));
}

std::shared_ptr<ZenShape> ZenShape::mirrorYZ() {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_mirrorYZ()));
}

std::shared_ptr<ZenShape> ZenShape::mirrorXZ() {
	return std::shared_ptr<ZenShape>(new ZenTransformShape(get_spointer(), trans_mirrorXZ()));
}
*/
std::shared_ptr<ZenSolid> operator+ (const ZenSolid& lhs, const ZenSolid& rhs) {
	return std::shared_ptr<ZenSolid>(new ZenUnion(lhs.get_spointer(), rhs.get_spointer()));
}

std::shared_ptr<ZenSolid> operator- (const ZenSolid& lhs, const ZenSolid& rhs) {
	return std::shared_ptr<ZenSolid>(new ZenDifference(lhs.get_spointer(), rhs.get_spointer()));
}

std::shared_ptr<ZenSolid> operator^ (const ZenSolid& lhs, const ZenSolid& rhs) {
	return std::shared_ptr<ZenSolid>(new ZenIntersect(lhs.get_spointer(), rhs.get_spointer()));
}

std::shared_ptr<ZenSolid> ZenSolid::get_spointer() const {
	return std::dynamic_pointer_cast<ZenSolid, ZenCadObject>((const_cast<ZenSolid*>(this))->shared_from_this());
}