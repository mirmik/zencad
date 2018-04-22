#ifndef DZENCAD_WIDGET_H
#define DZENCAD_WIDGET_H

#include <zencad/topo.h>

void display(std::shared_ptr<ZenShape> ptr);
void display_native(const TopoDS_Shape& shp);
void show();

#endif