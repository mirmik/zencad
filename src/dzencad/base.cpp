#include <dzencad/base.h>
#include <gxx/print.h>

#include <iostream>

uint64_t DzenCadObject::evaluate_hash() {

}

void DzenCadObject::prepare() {
	if (!prepared) {
		gxx::fprintln("{}::doit", class_name());
		doit();
		prepared = true;
	}
}

void DzenCadObject::doit() {
	gxx::fprintln("{} doesn't implement doit method", class_name());
	exit(-1);
	//throw GXX_NOT_IMPLEMENTED;
}

DzenCadObject::~DzenCadObject() {

}