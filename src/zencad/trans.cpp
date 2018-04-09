#include <zencad/trans.h>
#include <gp_Ax1.hxx>
#include <gp_Ax2.hxx>
#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>

void ZenTranslate::doit() {
	trsf.SetTranslation(gp_Vec(x,y,z));
}

void ZenRotate::doit() {
	trsf.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Vec(ax,ay,az)), angle);
}

void ZenAxisMirror::doit() {
	trsf.SetMirror(gp_Ax1(gp_Pnt(0,0,0), gp_Vec(ax,ay,az)));
}

void ZenPlaneMirror::doit() {
	trsf.SetMirror(gp_Ax2(gp_Pnt(0,0,0), gp_Vec(ax,ay,az)));
}
/*
void ZenTransformMultiply::doit() {
	trsf = a->trsf.Multiplied(b->trsf);
}*/