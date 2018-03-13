#ifndef DZENCAD_CACHE_H
#define DZENCAD_CACHE_H

#include <string>
#include <set>

extern std::set<std::string> zencache_set;

bool zencache_is_enabled();
void zencache_enable(const std::string& path);
void zencache_disable();
std::string zencache_path();

#endif