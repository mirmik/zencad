#include <dzencad/base.h>
//#include <gxx/exception.h>

#include <iostream>

uint64_t DzenCadObject::evaluate_hash() {

}

void DzenCadObject::prepare() {
	if (!prepared) {
		doit();
		prepared = true;
	}
}

void DzenCadObject::doit() {
	std::cout << "DzenCadObject::doit" << std::endl;
	exit(0);
	//throw GXX_NOT_IMPLEMENTED;
}

DzenCadObject::~DzenCadObject() {

}