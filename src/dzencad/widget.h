#ifndef DZENCAD_WIDGET_H
#define DZENCAD_WIDGET_H

#include <dzencad/topo.h>

void display(std::shared_ptr<DzenShape> ptr);
void display_native(const TopoDS_Shape& shp);
void show();

#endif