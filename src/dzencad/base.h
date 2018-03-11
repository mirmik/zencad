#ifndef DZENCAD_BASE_H
#define DZENCAD_BASE_H

#include <inttypes.h>
#include <memory>

struct DzenCadObject : public std::enable_shared_from_this<DzenCadObject> {
	bool prepared = false;

	virtual uint64_t evaluate_hash();
	virtual void prepare();
	virtual void doit();
	virtual const char* class_name() { return "DzenCadObject"; }
	
	virtual ~DzenCadObject();
};

#endif