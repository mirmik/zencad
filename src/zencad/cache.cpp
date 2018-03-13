#include <zencad/cache.h>
#include <gxx/osutil/file.h>
#include <gxx/panic.h>
#include <gxx/print.h>
#include <iterator>

bool __cache_is_enabled = false;
std::string dirpath;
std::set<std::string> zencache_set;

std::string zencache_path() {
	return dirpath;
}

bool zencache_is_enabled() {
	return __cache_is_enabled;
}

void zencache_enable(const std::string& path) {
	dirpath = path;
	__cache_is_enabled = true;

	if (gxx::osutil::isexist(path)) {
		if (!gxx::osutil::isdir(path)) {
			gxx::fprintln("{} isn't directory", path);
			gxx::panic();
		}
		auto lst = gxx::osutil::listdir(path);
		zencache_set.insert(lst.begin(), lst.end());
	}
	else {
		gxx::osutil::mkdir(path, 0777);
	}
}

void zencache_disable() {
	__cache_is_enabled = false;
}