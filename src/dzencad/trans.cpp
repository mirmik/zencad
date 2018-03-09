#include <dzencad/trans.h>
#include <gp_Ax1.hxx>
#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>

void DzenTranslate::doit() {
	trsf.SetTranslation(gp_Vec(x,y,z));
}

void DzenRotation::doit() {
	trsf.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Vec(ax,ay,az)), angle);
}

void DzenTransformMultiply::doit() {
	trsf = a->trsf.Multiplied(b->trsf);
}