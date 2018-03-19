#include <zencad/solid.h>
#include <zencad/face.h>
#include <zencad/wire.h>
#include <TopExp_Explorer.hxx>
#include <TopAbs.hxx>

void ZenLinearExtrude::doit() { 
	BRepPrimAPI_MakePrism mk(fc->native(), vec);
	m_native = mk; 
}

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
	}
};