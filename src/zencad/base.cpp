#include <zencad/base.h>
#include <zencad/cache.h>

#include <gxx/print.h>
#include <gxx/print/stdprint.h>
#include <gxx/util/text.h>

#include <iostream>
#include <fstream>

void ZenCadObject::prepare() {
	gxx::println("prepare");
	if (prepared) return;

	if (setted_hash == 0) {
		gxx::fprintln("warn: {} in class {}", gxx::text::bright_red("uninitialized hash"), gxx::text::bright_yellow(class_name()));
	}

	if (!prepared) {
		//if (zencache_is_enabled() && setted_hash1 && setted_hash2) {
		if (zencache_is_enabled() && setted_hash) {
			std::string hashstr = get_hash_base64();
			std::string filepath = gxx::format("{}/{}.dump", zencache_path(), hashstr);		
			
			if (zencache_set.find(hashstr) != zencache_set.end()) {
				gxx::fprintln("load data from cache {}", class_name());
				std::ifstream file(filepath, std::ios::binary);
				load_cached(file);
				//deserialize_from_stream(file);
			} else {
				//gxx::fprintln("cache miss {}", class_name());
				doit();	
				std::ofstream file(filepath, std::ios::binary);
				dump(file);
				//serialize_to_stream(file);
			}
		} else {
			doit();
		}

		prepared = true;
	}
}

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
*/
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


void ZenCadObject::initialize_hash() {
	ZenVisitor_Hashes alg;
	vreflect(alg);
	hash = alg.evaluate_current_hash();
	setted_hash = true;
}