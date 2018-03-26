#ifndef DZENCAD_BASE_H
#define DZENCAD_BASE_H

#include <typeinfo>
#include <typeindex>

#include <gxx/exception.h>
#include <gxx/util/base64.h>
#include <inttypes.h>
#include <memory>
#include <iostream>
#include <vector>

#include <zencad/cache.h>

struct ZenCadObject;

struct ZenVisitor {
	virtual void operator & (const ZenCadObject& obj) = 0;	
	virtual void operator & (double obj) = 0;	
};

struct ZenCadObject : public std::enable_shared_from_this<ZenCadObject> {
	bool prepared = false;
	//bool setted_hash1 = false;
	//bool setted_hash2 = false;

	bool setted_hash = false;
	size_t hash;
	
	//size_t hash1;
	//size_t hash2;

	ZenCadObject() = default;

	//size_t set_hash1(size_t hash1) { setted_hash1 = true; this->hash1 = hash1; }
	//size_t set_hash2(size_t hash2) { setted_hash2 = true; this->hash2 = hash2; }
	virtual void prepare();
	virtual void doit() { throw GXX_NOT_IMPLEMENTED; }
	virtual const char* class_name() const { throw GXX_NOT_IMPLEMENTED; }
	virtual ~ZenCadObject(){};

	//size_t get_hash1() const { assert(setted_hash1); return hash1; };
	//size_t get_hash2() const { assert(setted_hash2); return hash2; };
	std::string get_hash_base64() const {
		assert(setted_hash);
		return gxx::base64url_encode((const uint8_t*)&hash, sizeof(size_t));
	}

	void dump(std::ostream& out);
	void load_cached(std::istream& in);

	virtual void serialize_to_stream(std::ostream& out) { 
		gxx::println(class_name());
		throw GXX_NOT_IMPLEMENTED; 
	}

	virtual void deserialize_from_stream(std::istream& out) { 
		gxx::println(class_name());
		throw GXX_NOT_IMPLEMENTED; 
	}

	virtual void vreflect(ZenVisitor& visitor) { 
		gxx::println(class_name());
		throw GXX_NOT_IMPLEMENTED; 
	}

	void initialize_hash();

	int vreflect_count();
	void vreflect_print_info();
	
	//void vreflect_hashes();
	size_t vreflect_evaluate_hash1();
	size_t vreflect_evaluate_hash2();

	//virtual uint64_t hash() { throw GXX_NOT_IMPLEMENTED; }
};

template <typename T>
static size_t make_hash(const T &v) {
    return std::hash<T>()(v);
}

struct ZenVisitor_Count : public ZenVisitor {
	int count;
	void operator & (const ZenCadObject& obj) override { ++count; }	
	void operator & (double obj) override { ++count; }
};

struct ZenVisitor_PrintClass : public ZenVisitor {
	void operator & (const ZenCadObject& obj) override { gxx::print(obj.class_name()); gxx::putchar(' '); }	
	void operator & (double obj) override { gxx::print("double "); }
};    

/*struct ZenVisitor_Hash1 : public ZenVisitor {
	size_t hash;
	bool first = true;
	void add(size_t h) {
		if (first) { first = false; hash = h; }
		else hash ^= h;
	}
	void operator & (const ZenCadObject& obj) override { add(obj.hash1); }	
	void operator & (double obj) override { add(std::hash<double>()(obj)); }
};    

struct ZenVisitor_Hash2 : public ZenVisitor {
	size_t hash;
	bool first = true;
	void add(size_t h) {
		if (first) { first = false; hash = h; }
		else hash += h;
	}
	void operator & (const ZenCadObject& obj) override { add(obj.hash2); }	
	void operator & (double obj) override { add(std::hash<double>()(obj)); }
};*/


struct ZenVisitor_Hashes : public ZenVisitor {
	std::vector<size_t> hashes;
	void operator & (const ZenCadObject& obj) override { hashes.push_back(obj.hash); }	
	void operator & (double obj) override { hashes.push_back(std::hash<double>()(obj)); }

	size_t evaluate_current_hash() {
		size_t hash = hashes[0];
		for ( int i = 1; i < hashes.size(); ++i ) {
			hash ^= hashes[i];
		}
		return hash;
	}
};

#endif