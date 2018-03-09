#include <dzencad/base.h>

#include <boost/python.hpp>
using namespace boost::python;

#include <gxx/exception.h>

uint64_t DzenCadObject::evaluate_hash() {

}

void DzenCadObject::prepare() {
	if (!prepared) {
		doit();
		prepared = true;
	}
}

void DzenCadObject::doit() {
	throw GXX_NOT_IMPLEMENTED;
}

DzenCadObject::~DzenCadObject() {

}