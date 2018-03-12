#ifndef DZENCAD_CACHE_H
#define DZENCAD_CACHE_H

#include <string>
#include <set>

extern std::set<std::string> dzencache_set;

bool dzencache_is_enabled();
void dzencache_enable(const std::string& path);
void dzencache_disable();
std::string dzencache_path();

#endif