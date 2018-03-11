#include <dzencad/wire.h>
#include <dzencad/face.h>

std::shared_ptr<DzenFace> DzenWire::make_face() {
	return std::shared_ptr<DzenFace>(new DzenWireFace(this->get_spointer()));
}