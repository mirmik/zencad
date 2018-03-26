#ifndef DZENCAD_TOPO_H
#define DZENCAD_TOPO_H

#include <zencad/base.h>

#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Edge.hxx>
#include <BinTools_ShapeSet.hxx>
#include <BinTools.hxx>

#include <zencad/boolops.h>
#include <zencad/trans.h>
#include <gxx/print.h>

#include <memory>
#include <vector>

class ZenTransformShape;
class ZenTransform;

struct ZenShape : public ZenCadObject {
	const TopoDS_Shape& native() {
		if (!prepared) prepare();
		return m_native;
	}

	void serialize_to_stream(std::ostream& out) override {
		 // An example how to use BinTools_ShapeSet can be found in BinMNaming_NamedShapeDriver.cxx
    	BinTools_ShapeSet theShapeSet;
    	if (m_native.IsNull()) {
    	    theShapeSet.Add(m_native);
    	    theShapeSet.Write(out);
    	    BinTools::PutInteger(out, -1);
    	    BinTools::PutInteger(out, -1);
    	    BinTools::PutInteger(out, -1);
    	}
    	else {
    	    Standard_Integer shapeId = theShapeSet.Add(m_native);
    	    Standard_Integer locId = theShapeSet.Locations().Index(m_native.Location());
    	    Standard_Integer orient = static_cast<int>(m_native.Orientation());
	
    	    theShapeSet.Write(out);
    	    BinTools::PutInteger(out, shapeId);
    	    BinTools::PutInteger(out, locId);
    	    BinTools::PutInteger(out, orient);
    	}
	}

	void deserialize_from_stream(std::istream& in) override {
	    BinTools_ShapeSet theShapeSet;
	    theShapeSet.Read(in);
	    Standard_Integer shapeId=0, locId=0, orient=0;
	    BinTools::GetInteger(in, shapeId);
	    if (shapeId <= 0 || shapeId > theShapeSet.NbShapes())
	        return;
	
	    BinTools::GetInteger(in, locId);
	    BinTools::GetInteger(in, orient);
	    TopAbs_Orientation anOrient = static_cast<TopAbs_Orientation>(orient);
	
	    try {
	        m_native = theShapeSet.Shape(shapeId);
	        m_native.Location(theShapeSet.Locations().Location (locId));
	        m_native.Orientation (anOrient);
	    }
	    catch (Standard_Failure) {
	        gxx::println("Failed to read shape from binary stream");
	        exit(-1);	
	    }
	}

	void dump_binary(std::string path) {
		prepare();
		std::ofstream file(path, std::ios::binary);
		serialize_to_stream(file);
	}

	//void load_binary(std::string path) {
	//	std::ifstream file(path, std::ios::binary);
	//	deserialize_from_stream(file);
	//}


/*void TopoShape::exportBinary(std::ostream& out)
{
    // An example how to use BinTools_ShapeSet can be found in BinMNaming_NamedShapeDriver.cxx
    BinTools_ShapeSet theShapeSet;
    if (this->_Shape.IsNull()) {
        theShapeSet.Add(this->_Shape);
        theShapeSet.Write(out);
        BinTools::PutInteger(out, -1);
        BinTools::PutInteger(out, -1);
        BinTools::PutInteger(out, -1);
    }
    else {
        Standard_Integer shapeId = theShapeSet.Add(this->_Shape);
        Standard_Integer locId = theShapeSet.Locations().Index(this->_Shape.Location());
        Standard_Integer orient = static_cast<int>(this->_Shape.Orientation());

        theShapeSet.Write(out);
        BinTools::PutInteger(out, shapeId);
        BinTools::PutInteger(out, locId);
        BinTools::PutInteger(out, orient);
    }
}*/


	//virtual TopoDS_Shape shape() = 0;

	//std::shared_ptr<ZenShape> transform(std::shared_ptr<ZenTransform> trsf);
	//std::shared_ptr<ZenShape> translate(double x, double y, double z);
	//
	//std::shared_ptr<ZenShape> up(double z);
	//std::shared_ptr<ZenShape> down(double z);
	//std::shared_ptr<ZenShape> right(double x);
	//std::shared_ptr<ZenShape> left(double x);
	//std::shared_ptr<ZenShape> forw(double y);
	//std::shared_ptr<ZenShape> back(double y);
//
	//std::shared_ptr<ZenShape> rotateX(double a);
	//std::shared_ptr<ZenShape> rotateY(double a);
	//std::shared_ptr<ZenShape> rotateZ(double a);
//
	//std::shared_ptr<ZenShape> mirrorX();
	//std::shared_ptr<ZenShape> mirrorY();
	//std::shared_ptr<ZenShape> mirrorZ();
//
	//std::shared_ptr<ZenShape> mirrorXY();
	//std::shared_ptr<ZenShape> mirrorYZ();
	//std::shared_ptr<ZenShape> mirrorXZ();

protected:
	TopoDS_Shape m_native;
};


struct ZenVertex;
struct ZenEdge;
struct ZenWire;
struct ZenFace;
struct ZenSolid;

template <typename Self> struct ZenShapeExplorer;

template <typename Self>
struct ZenShapeInterface : public ZenShape {
	//TopoDS_Shape shape() override { 
	//	Self* self = static_cast<Self*>(this);
	//	return self->native; 
	//};

	std::shared_ptr<Self> get_spointer() const {
		Self* self = static_cast<Self*>( const_cast<ZenShapeInterface*>(this) );
		return std::dynamic_pointer_cast<Self,ZenCadObject>(self->shared_from_this());
	}	

	std::shared_ptr<Self> transform(std::shared_ptr<ZenTransform> trsf) {
		return std::shared_ptr<Self>(new ZenTransformed<Self>(get_spointer(), trsf));
	}

	std::shared_ptr<Self> translate(double x, double y, double z) {
		return transform(std::shared_ptr<ZenTransform>(new ZenTranslate(x, y, z)));
	}
	
	std::shared_ptr<Self> right	(double x) 	{ return translate(  x,  0,  0); }
	std::shared_ptr<Self> left	(double x) 	{ return translate( -x,  0,  0); }
	std::shared_ptr<Self> forw	(double y) 	{ return translate(  0,  y,  0); }
	std::shared_ptr<Self> back	(double y) 	{ return translate(  0, -y,  0); }
	std::shared_ptr<Self> up	(double z)	{ return translate(  0,  0,  z); }
	std::shared_ptr<Self> down	(double z) 	{ return translate(  0,  0, -z); }
	
	std::shared_ptr<Self> rotateX(double a) { return transform(trans_rotateX(a)); }
	std::shared_ptr<Self> rotateY(double a) { return transform(trans_rotateY(a)); }
	std::shared_ptr<Self> rotateZ(double a) { return transform(trans_rotateZ(a)); }

	std::shared_ptr<Self> mirrorX() { return transform(trans_mirrorX()); }
	std::shared_ptr<Self> mirrorY() { return transform(trans_mirrorY()); }
	std::shared_ptr<Self> mirrorZ() { return transform(trans_mirrorZ()); }

	std::shared_ptr<Self> mirrorXY() { return transform(trans_mirrorXY()); }
	std::shared_ptr<Self> mirrorYZ() { return transform(trans_mirrorYZ()); }
	std::shared_ptr<Self> mirrorXZ() { return transform(trans_mirrorXZ()); }

	std::shared_ptr<ZenShapeExplorer<ZenWire>> wires() {
		return std::shared_ptr<ZenShapeExplorer<ZenWire>>(new ZenShapeExplorer<ZenWire>(get_spointer()));
	}

	std::shared_ptr<ZenShapeExplorer<ZenVertex>> vertexs() {
		return std::shared_ptr<ZenShapeExplorer<ZenVertex>>(new ZenShapeExplorer<ZenVertex>(get_spointer()));
	}
};

template <typename Self> 
struct ZenBooleanShapeInterface : public ZenShapeInterface<Self> {
	std::shared_ptr<Self> operator+ (const Self& rhs) const {
		return std::shared_ptr<Self>(new ZenUnion<Self>(ZenShapeInterface<Self>::get_spointer(), rhs.get_spointer()));
	}

	std::shared_ptr<Self> operator- (const Self& rhs) const {
		return std::shared_ptr<Self>(new ZenDifference<Self>(ZenShapeInterface<Self>::get_spointer(), rhs.get_spointer()));
	}

	std::shared_ptr<Self> operator^ (const Self& rhs) const {
		return std::shared_ptr<Self>(new ZenIntersect<Self>(ZenShapeInterface<Self>::get_spointer(), rhs.get_spointer()));
	}
};

template <typename Topo>
std::shared_ptr<Topo> zen_load(std::string path) {
	std::shared_ptr<Topo> topo(new Topo);
	std::ifstream file(path, std::ios::binary);
	topo->deserialize_from_stream(file);
	topo->prepared = true;
	return topo;
}

struct ZenSolid : public ZenBooleanShapeInterface<ZenSolid> {
	const char* class_name() { return "ZenSolid"; }
};

#include <BRepBuilderAPI_MakeVertex.hxx>
struct ZenVertex : ZenShapeInterface<ZenVertex> {
	using native_type = TopoDS_Vertex;
	static constexpr TopAbs_ShapeEnum shape_topabs = TopAbs_VERTEX;
	static native_type shape_convert(const TopoDS_Shape& shp) { return TopoDS::Vertex(shp); }

	double x,y,z;
	const char* class_name() const override { return "ZenVertex"; }
	std::shared_ptr<ZenVertex> vtx;
	ZenVertex(){}
	ZenVertex(double x, double y, double z) : x(x), y(y), z(z) {}
	void doit() override {m_native = BRepBuilderAPI_MakeVertex(gp_Pnt(x,y,z)); }
};


#include <TopExp_Explorer.hxx>
template <typename Self> struct ZenFromExplorer;

template <typename Self>
struct ZenShapeExplorer : public ZenCadObject {
	const char* class_name() const override { return "ZenShapeExplorer"; }
	std::vector<typename Self::native_type> shps;
	std::shared_ptr<ZenShape> src;
	ZenShapeExplorer(std::shared_ptr<ZenShape> src) : src(src) {}
	void doit() override { 
		for(TopExp_Explorer nexp(src->native(), Self::shape_topabs); nexp.More(); nexp.Next()) {	
			shps.push_back(Self::shape_convert(nexp.Current()));			
		}
	}
	size_t size() {
		prepare();
		return shps.size();
	}

	std::shared_ptr<Self> getitem(int n) {
		auto sptr = std::dynamic_pointer_cast<ZenShapeExplorer, ZenCadObject>(shared_from_this());
		return std::shared_ptr<Self>(new ZenFromExplorer<Self>(sptr, n));
	}
};

template <typename Self>
struct ZenFromExplorer : public Self {
	int n;
	std::shared_ptr<ZenShapeExplorer<Self>> exp;
	ZenFromExplorer(std::shared_ptr<ZenShapeExplorer<Self>> exp, int n) : exp(exp), n(n) {}
	void doit() {
		exp->prepare();
		Self::m_native = exp->shps[n];
	}
};

#endif