#include <dzencad/cache.h>

bool __cache_is_enabled = false;

bool dzencache_is_enabled() {
	return __cache_is_enabled;
}

void dzencache_enable() {
	__cache_is_enabled = true;
}

void dzencache_disable() {
	__cache_is_enabled = false;
}