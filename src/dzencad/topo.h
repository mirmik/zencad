#ifndef DZENCAD_TOPO_H
#define DZENCAD_TOPO_H

#include <dzencad/base.h>

#include <TopoDS_Shape.hxx>

struct DzenShape : public DzenCadObject {
	TopoDS_Shape native;
};

struct DzenSolid : public DzenShape {};

#endif