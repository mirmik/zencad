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
	//Хеш используется для кеширования результатов длинных вычислений.
	size_t hash;

	//В случае колизии кеша, объект сохраняется с уникальным минором.
	uint8_t minor;

	//Если установлен этот флаг, поле m_native валидно.
	bool prepared = false;

	//Если установлен этот флаг, поле хэша валидно.
	bool setted_hash = false;

	//Если установлен этот флаг, поле хэша валидно.
	bool checked_hash = false;

	//Расчитать хэш объекта.
	void initialize_hash();

	//Подготовить данные для последующего использования. Если данные уже готовы, ничего не делать.
	void prepare();
	
	//Записать хешы зависимостей в поток. 
	void info_dump(std::ostream& out);

	//Пропустить часть потока по размеру зависимостей.
	void info_skip(std::istream& in);

	//Проверить хэши зависимостей в потоке.
	bool info_check(std::istream& in);

	//Записать данные объекта в поток.
	virtual void dump(std::ostream& out) { PANIC_TRACED(); }

	//Считать данные объекта из потока.
	virtual void load(std::istream& in) { PANIC_TRACED(); }

	//Выполнение операции.
	virtual void doit() { PANIC_TRACED(); }
	
	//Возвращает имя класса.
	virtual const char* class_name() const { PANIC_TRACED(); }

	//Обход зависимостей объекта. Для реализации рефлексии.  
	virtual void vreflect(ZenVisitor& visitor) { PANIC_TRACED(); }

	//Методы, приминяющие рефлексию.

	//Количество зависимостей.
	int vreflect_deps_count();
	
	//Количество сложных зависимостей.
	int vreflect_objdeps_count();

	//void vreflect_print_info();
};

/*template <typename Self> class ZenCadObject_Typed : public ZenCadObject {
public:
};*/

/*template <typename T> static size_t make_hash(const T &v) { return std::hash<T>()(v); }

struct ZenVisitor_Count : public ZenVisitor {
	int count;
	void operator & (const ZenCadObject& obj) override { ++count; }	
	void operator & (double obj) override { ++count; }
};*/

/*struct ZenVisitor_PrintClass : public ZenVisitor {
	void operator & (const ZenCadObject& obj) override { gxx::print(obj.class_name()); gxx::putchar(' '); }	
	void operator & (double obj) override { gxx::print("double "); }
};*/    

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
	size_t evaluate_current_hash();
};

#endif