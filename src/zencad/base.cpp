#include <zencad/base.h>
#include <zencad/cache.h>

#include <gxx/print.h>
#include <gxx/print/stdprint.h>
#include <gxx/util/text.h>

#include <iostream>
#include <fstream>

void ZenCadObject::prepare() {
	if (prepared) return;

	if (setted_hash1 == 0 || setted_hash2 == 0) {
		gxx::fprintln("warn: {} in class {}", gxx::text::bright_red("uninitialized hash"), gxx::text::bright_yellow(class_name()));
	}

	if (!prepared) {
		if (zencache_is_enabled() && setted_hash1 && setted_hash2) {
			std::string hashstr = get_hash_base64();
			std::string filepath = gxx::format("{}/{}.dump", zencache_path(), hashstr);		
			
			if (zencache_set.find(hashstr) != zencache_set.end()) {
				//gxx::fprintln("load data from cache {}", class_name());
				std::ifstream file(filepath, std::ios::binary);
				deserialize_from_stream(file);
			} else {
				//gxx::fprintln("cache miss {}", class_name());
				doit();	
				std::ofstream file(filepath, std::ios::binary);
				serialize_to_stream(file);
			}
		} else {
			doit();
		}

		prepared = true;
	}
}