#ifndef DZENCAD_CACHE_H
#define DZENCAD_CACHE_H

#include <string>
#include <set>

#include <zencad/base.h>

extern std::set<std::string> zencache_set;

bool zencache_is_enabled();
void zencache_enable(const std::string& path);
void zencache_disable();
std::string zencache_path();

//std::string check_cache(ZenCadObject& zobj);

#endif