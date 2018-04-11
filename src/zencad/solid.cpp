#include <zencad/solid.h>
#include <zencad/face.h>
#include <zencad/wire.h>
#include <TopExp_Explorer.hxx>
#include <TopAbs.hxx>

#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeTorus.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRepPrimAPI_MakeWedge.hxx>
#include <BRepOffsetAPI_ThruSections.hxx>
#include <BRepOffsetAPI_MakePipe.hxx>

ZenBox::ZenBox(double x, double y, double z, bool center) : x(x), y(y), z(z), center(center) { initialize_hash(); }
ZenCylinder::ZenCylinder(double r, double h, bool center) : r(r), h(h), center(center) { initialize_hash(); }
ZenSphere::ZenSphere(double r) : r(r) { initialize_hash(); }
ZenTorus::ZenTorus(double r1, double r2) : r1(r1), r2(r2) { initialize_hash(); }

ZenCone::ZenCone(double r1, double r2, double h, bool center) : r1(r1), r2(r2), h(h), center(center) { initialize_hash(); }

const char* ZenBox::class_name() const { return "ZenBox"; }
const char* ZenSphere::class_name() const { return "ZenSphere"; }
const char* ZenCylinder::class_name() const { return "ZenCylinder"; }
const char* ZenTorus::class_name() const { return "ZenTorus"; }
const char* ZenCone::class_name() const { return "ZenCone"; }
const char* ZenLinearExtrude::class_name() const { return "ZenLinearExtrude"; }

void ZenBox::doit() { 
	if (!center) {
		m_native = BRepPrimAPI_MakeBox(x, y, z).Solid(); 
	} else {
		gp_Ax2 ax2(gp_Pnt(-x/2,-y/2,-z/2), gp_Vec(0,0,1));
		m_native = BRepPrimAPI_MakeBox(ax2, x, y, z).Solid(); 			
	}
}

void ZenCylinder::doit() { 
	if (!center) {
		m_native = BRepPrimAPI_MakeCylinder(r, h).Solid(); 
	} else {
		gp_Ax2 ax2(gp_Pnt(0,0,-h/2), gp_Vec(0,0,1));
		m_native = BRepPrimAPI_MakeCylinder(ax2, r, h).Solid(); 		
	}
}

void ZenCone::doit() { 
	if (!center) {
		m_native = BRepPrimAPI_MakeCone(r1, r2, h).Solid(); 
	} else {
		gp_Ax2 ax2(gp_Pnt(0,0,-h/2), gp_Vec(0,0,1));
		m_native = BRepPrimAPI_MakeCone(ax2, r1, r2, h).Solid(); 		
	}
}

void ZenSphere::doit() { m_native = BRepPrimAPI_MakeSphere(r).Solid(); }
void ZenTorus::doit() { m_native = BRepPrimAPI_MakeTorus(r1,r2).Solid(); }

void ZenBox::vreflect(ZenVisitor& v) { v&x; v&y; v&z; v&center; }
void ZenSphere::vreflect(ZenVisitor& v) { v&r; }
void ZenCylinder::vreflect(ZenVisitor& v) { v&r; v&h; v&center; }
void ZenTorus::vreflect(ZenVisitor& v) { v&r1; v&r2; }
void ZenCone::vreflect(ZenVisitor& v) { v&r1; v&r2; v&h; v&center; }
void ZenLinearExtrude::vreflect(ZenVisitor& v) { v&*fc; v&vec; }	

/*
void ZenBox::doit() { 
	if (!center) {
		set_native(BRepPrimAPI_MakeBox(x, y, z).Solid()); 
	} else {
		gp_Ax2 ax2(gp_Pnt(-x/2,-y/2,-z/2), gp_Vec(0,0,1));
		set_native(BRepPrimAPI_MakeBox(ax2, x, y, z).Solid()); 			
	}
}

void ZenBox::vreflect(ZenVisitor& v) {
	v & x; v & y; v & z; v & center;
}



	ZenSphere(double r) : r(r);
	void doit() override;
	//void doit() override { m_native = BRepPrimAPI_MakeSphere(r).Solid(); }
};




struct ZenCylinder : public ZenSolid {
	const char* class_name() const override { return "ZenCylinder"; }
	double r, h;
	ZenCylinder(double r, double h) : r(r), h(h) { }
		//set_hash1(typeid(this).hash_code() ^ make_hash(r) ^ make_hash(h));
		//set_hash2(typeid(this).hash_code() + make_hash(r) + make_hash(h));}
	void doit() override { m_native = BRepPrimAPI_MakeCylinder(r, h).Solid(); }
};

struct ZenTorus : public ZenSolid {
	const char* class_name() const override { return "ZenTorus"; }
	double r1, r2;
	ZenTorus(double r1, double r2) : r1(r1), r2(r2) {}
		//set_hash1(typeid(this).hash_code() ^ make_hash(r1) ^ make_hash(r2));
		//set_hash2(typeid(this).hash_code() + make_hash(r1) + make_hash(r2));}
};



/*


*/
ZenLinearExtrude::ZenLinearExtrude(std::shared_ptr<ZenFace> fc, double z) : fc(fc), vec(0,0,z) {
	initialize_hash();
}

ZenLinearExtrude::ZenLinearExtrude(std::shared_ptr<ZenFace> fc, ZenVector3 v) : fc(fc), vec(v) {
	initialize_hash();
}
/*






struct ZenSphere : public ZenSolid {
	const char* class_name() const override;// { return "ZenSphere"; }
	double r;
	ZenSphere(double r) : r(r);
	void doit() override;
	//void doit() override { m_native = BRepPrimAPI_MakeSphere(r).Solid(); }
};

struct ZenCylinder : public ZenSolid {
	const char* class_name() const override { return "ZenCylinder"; }
	double r, h;
	ZenCylinder(double r, double h) : r(r), h(h) { }
		//set_hash1(typeid(this).hash_code() ^ make_hash(r) ^ make_hash(h));
		//set_hash2(typeid(this).hash_code() + make_hash(r) + make_hash(h));}
	void doit() override { m_native = BRepPrimAPI_MakeCylinder(r, h).Solid(); }
};

struct ZenTorus : public ZenSolid {
	const char* class_name() const override { return "ZenTorus"; }
	double r1, r2;
	ZenTorus(double r1, double r2) : r1(r1), r2(r2) {}
		//set_hash1(typeid(this).hash_code() ^ make_hash(r1) ^ make_hash(r2));
		//set_hash2(typeid(this).hash_code() + make_hash(r1) + make_hash(r2));}
	void doit() override { m_native = BRepPrimAPI_MakeTorus(r1,r2).Solid(); }
};

struct ZenWedge : public ZenSolid {
	const char* class_name() const override { return "ZenWedge"; }
	double x, y, z, ltx;
	ZenWedge(double x, double y, double z, double ltx) : x(x), y(y), z(z), ltx(ltx) {}
		//set_hash1(typeid(this).hash_code() ^ make_hash(x) ^ make_hash(y) ^ make_hash(z) ^ make_hash(ltx));
		//set_hash2(typeid(this).hash_code() + make_hash(x) + make_hash(y) + make_hash(z) + make_hash(ltx));}
	void doit() override { m_native = BRepPrimAPI_MakeWedge(x,y,z,ltx).Solid(); }
};
*/
/*struct ZenLinearExtrude : public ZenSolid {
	const char* class_name() const override { return "ZenLinearExtrude"; }
	gp_Vec vec;
	std::shared_ptr<ZenFace> fc;
	ZenLinearExtrude(std::shared_ptr<ZenFace> fc, double z) : fc(fc), vec(0,0,z) {}
	ZenLinearExtrude(std::shared_ptr<ZenFace> fc, ZenVector3 v) : fc(fc), vec(v.Vec()) {}
	void doit() override;
};


struct ZenLoft : public ZenSolid {
	const char* class_name() const override { return "ZenLoft"; }
	std::vector<std::shared_ptr<ZenShape>> shapes;

	ZenLoft(pybind11::list args) {
    	for (auto item : args) {
    		auto pnt = item.cast<std::shared_ptr<ZenShape>>();
    		shapes.push_back(pnt);
    	}
	}

	void doit() override;
};


struct ZenPipe : public ZenSolid {
	const char* class_name() const override { return "ZenPipe"; }
	std::shared_ptr<ZenWire> path;
	std::shared_ptr<ZenShape> profile;

	ZenPipe(std::shared_ptr<ZenWire> path, std::shared_ptr<ZenShape> profile) 
		: profile(profile), path(path) 
	{
    	
	}

	void doit() override;
};*/















void ZenLinearExtrude::doit() { 
	BRepPrimAPI_MakePrism mk(fc->native(), vec.Vec());
	m_native = mk; 
}
/*
void ZenLoft::doit() {
	BRepOffsetAPI_ThruSections tsect(true, true);
	for (auto& shp : shapes) {
		TopoDS_Shape nshp = shp->native();

		switch(nshp.ShapeType()) {
			case TopAbs_VERTEX: 
				tsect.AddVertex(TopoDS::Vertex(nshp));
				gxx::println("vertex");
				break; 

			case TopAbs_WIRE: 
				tsect.AddWire(TopoDS::Wire(nshp));
				gxx::println("wire");
				break; 

			case TopAbs_FACE: 
				{
					TopExp_Explorer expWire(TopoDS::Face(nshp), TopAbs_WIRE);
					tsect.AddWire(TopoDS::Wire(expWire.Current()));
				}
    	
				gxx::println("face");
				break; 

			case TopAbs_EDGE: 
				gxx::println("edge");
				break; 
		}

		tsect.Build();
		m_native = tsect;

		/*if (typeid(*shp) == typeid(ZenVertex)) {
			gxx::println("vertex");
		} 
		else if (typeid(*shp) == typeid(ZenWire)) {
			gxx::println("wire");
		} 
		else if (typeid(*shp) == typeid(ZenEdge)) {
			gxx::println("edge");
		} 
		else if (typeid(*shp) == typeid(ZenFace)) {
			gxx::println("face");
		} 
		else if (typeid(*shp) == typeid(ZenShape)) {
			gxx::println("shape");
		}*/
/*	}
};

void ZenPipe::doit() {
	BRepOffsetAPI_MakePipe builder(TopoDS::Wire(path->native()), profile->native());
	m_native = builder.Shape();

	/*BRepOffsetAPI_MakePipeShell builder(TopoDS::Wire(path->native()));
	builder.Add(profile->native());
	builder.SetMode(true);

	builder.Build();
	builder.MakeSolid();

	m_native = builder;*/
//}