#include <zencad/base.h>
#include <zencad/cache.h>

#include <gxx/print.h>
#include <gxx/print/stdprint.h>
#include <gxx/util/text.h>
#include <gxx/util/base64.h>
#include <gxx/osutil/file.h>

#include <iostream>
#include <fstream>


bool ZenCadObject::check_cache() {
	gxx::println("check_cache", class_name());
	if (checked_cache) return true;

	//gxx::println(class_name());
	assert(checked_cache == false && minor == 0);
	assert(setted_hash);

	hashstr = gxx::base64url_encode((const uint8_t*)&hash, sizeof(hash));

	checked_cache = true;
	while(true) {
		std::string filepath = gxx::format(minor ? "{}/{}_{}.dump" : "{}/{}.dump", zencache_path(), hashstr, minor);

		if (!gxx::osutil::isexist(filepath)) {
			gxx::fprintln("file {} isn't exist", gxx::text::yellow(filepath));
			cached = false;
			return false;
		} else {
			std::ifstream file(filepath, std::ios::binary);
			gxx::println("info_check for", class_name());
			cached = info_check(file) && vreflect_check_cache();
			file.close();
			if (cached) return true;		
		}

		minor++;
	}
}

void ZenCadObject::prepare() {
	gxx::fprintln("prepare {}", class_name());
	if (prepared) return;

	if (!setted_hash) {
		gxx::fprintln("warn: {} in class {}", 
			gxx::text::bright_red("uninitialized hash"), 
			gxx::text::bright_yellow(class_name())
		);
	}

	if (!prepared) {
		if (zencache_is_enabled() && setted_hash) {
			if (!checked_cache) check_cache();

			std::string filepath = gxx::format(minor ? "{}/{}_{}.dump" : "{}/{}.dump", zencache_path(), hashstr, minor);
			if (!cached) {
				gxx::fprintln("save to {}", filepath);

				doit();
				std::ofstream file(filepath, std::ios::binary);
				info_dump(file);
				dump(file);
				file.close();
			}

			else {
				gxx::fprintln("load from {}", filepath);

				std::ifstream file(filepath, std::ios::binary);
				info_skip(file);
				load(file);	
				file.close();			
			}	
		} else {
			doit();
		}

		prepared = true;
	}
}

bool ZenCadObject::vreflect_check_cache() {
	ZenVisitor_CheckCache alg;
	vreflect(alg);
	return alg.result;
}

bool ZenCadObject::info_check(std::istream& in) {
	ZenVisitor_Hashes alg;
	vreflect(alg);
	
	size_t ls = alg.hashes.size();
	size_t es;
	in.read((char*)&es, sizeof(size_t));
	
	if (ls != es) return false;
	for (size_t lh : alg.hashes) { 
		size_t eh;
		in.read((char*)&eh, sizeof(size_t)); 
		if (lh != eh) return false;		
	}

	return true;
}

void ZenCadObject::info_dump(std::ostream& out) {
	ZenVisitor_Hashes alg;
	vreflect(alg);
	auto s = alg.hashes.size();
	out.write((const char*)&s, sizeof(size_t));
	for (size_t h : alg.hashes) { 
		out.write((const char*)&h, sizeof(size_t)); 
	}
}

void ZenCadObject::info_skip(std::istream& in) {
	ZenVisitor_Hashes alg;
	vreflect(alg);
	in.ignore(sizeof(size_t));
	for (size_t h : alg.hashes) { 
		in.ignore(sizeof(size_t)); 
	}
}

/*
int ZenCadObject::vreflect_count() {
	ZenVisitor_Count alg;
	vreflect(alg);
	return alg.count;
}

void ZenCadObject::vreflect_print_info() {
	ZenVisitor_PrintClass alg;
	gxx::print(class_name());
	gxx::print("[ ");
	vreflect(alg);
	gxx::putchar(']');
	gxx::println();
}
/*
size_t ZenCadObject::vreflect_evaluate_hash1() {
	ZenVisitor_Hash1 alg;
	vreflect(alg);	
	return alg.hash;
}

size_t ZenCadObject::vreflect_evaluate_hash2() {
	ZenVisitor_Hash2 alg;
	vreflect(alg);	
	return alg.hash;	
}
*//*
void ZenCadObject::dump(std::ostream& out) {
	ZenVisitor_Hashes alg;
	vreflect(alg);
	out << alg.hashes.size();
	for (size_t h : alg.hashes) { out << h; }
	serialize_to_stream(out);
}

void ZenCadObject::load_cached(std::istream& in) {
	gxx::println("load_cached start");
	ZenVisitor_Hashes alg;
	vreflect(alg);
	
	size_t count;
	std::vector<size_t> cached_hashes;

	if (count != alg.hashes.size()) {
		gxx::panic("wrong count in hash");
	}
	in >> count;

	for (int i = 0; i < count; ++i) {
		size_t hash;
		in >> hash;
		if (hash != alg.hashes[i]) {
			gxx::panic("wrong hash in serialized vector");
		}
	}

	deserialize_from_stream(in);
	gxx::println("load_cached finish");
}

*/
void ZenCadObject::initialize_hash() {
	ZenVisitor_Hashes alg;
	vreflect(alg);
	hash = alg.evaluate() ^ typeid(*this).hash_code();
	setted_hash = true;
}

size_t ZenVisitor_Hashes::evaluate() {
	size_t hash = hashes[0];
	for ( int i = 1; i < hashes.size(); ++i ) {
		hash ^= hashes[i];
	}
	return hash;
}