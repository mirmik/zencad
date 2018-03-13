#ifndef DZENCAD_BASE_H
#define DZENCAD_BASE_H

#include <typeinfo>
#include <typeindex>

#include <gxx/exception.h>
#include <gxx/util/base64.h>
#include <inttypes.h>
#include <memory>
#include <iostream>

#include <zencad/cache.h>

struct ZenCadObject : public std::enable_shared_from_this<ZenCadObject> {
	bool prepared = false;
	bool setted_hash1 = false;
	bool setted_hash2 = false;
	size_t hash1;
	size_t hash2;

	ZenCadObject() = default;

	size_t set_hash1(size_t hash1) { setted_hash1 = true; this->hash1 = hash1; }
	size_t set_hash2(size_t hash2) { setted_hash2 = true; this->hash2 = hash2; }
	virtual void prepare();
	virtual void doit() { throw GXX_NOT_IMPLEMENTED; }
	virtual const char* class_name() { throw GXX_NOT_IMPLEMENTED; }
	virtual ~ZenCadObject(){};

	size_t get_hash1() const { assert(setted_hash1); return hash1; };
	size_t get_hash2() const { assert(setted_hash2); return hash2; };
	std::string get_hash_base64() const {
		assert(setted_hash1 && setted_hash2);
		return gxx::base64url_encode((const uint8_t*)&hash1, sizeof(size_t)) + gxx::base64url_encode((const uint8_t*)&hash2, sizeof(size_t));
	}

	virtual void serialize_to_stream(std::ostream& out) { 
		gxx::println(class_name());
		throw GXX_NOT_IMPLEMENTED; 
	}

	virtual void deserialize_from_stream(std::istream& out) { 
		gxx::println(class_name());
		throw GXX_NOT_IMPLEMENTED; 
	}

	//virtual uint64_t hash() { throw GXX_NOT_IMPLEMENTED; }
};

template <typename T>
static size_t make_hash(const T &v) {
    return std::hash<T>()(v);
}
    

#endif