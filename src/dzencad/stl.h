#ifndef DZENCAD_STL_H
#define DZENCAD_STL_H

#include <dzencad/base.h>
#include <StlAPI_Writer.hxx>

#include <gxx/print.h>

//class DzenStlMaker : public 

static inline void make_stl(std::string path, std::shared_ptr<DzenShape> sptr) {
	gxx::println("make_stl");
	sptr->prepare();

    StlAPI_Writer stl_writer;
    stl_writer.SetDeflection(0.1);
    stl_writer.RelativeMode() = false;
    stl_writer.Write(sptr->native, path.c_str());
}

#endif