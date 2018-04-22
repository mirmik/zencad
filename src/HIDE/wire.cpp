#include <zencad/wire.h>
#include <zencad/face.h>

#include <TopExp_Explorer.hxx>

std::shared_ptr<ZenFace> ZenWire::make_face() {
	return std::shared_ptr<ZenFace>(new ZenWireFace(this->get_spointer()));
}

std::shared_ptr<ZenFace> ZenEdge::make_face() {
	return std::shared_ptr<ZenFace>(new ZenEdgeFace(this->get_spointer()));
}

/*void ZenWiresFromFace::doit() { 
	for(TopExp_Explorer expWire(TopoDS::Face(fc->native()), TopAbs_WIRE); expWire.More(); expWire.Next()) {	
		wires.push_back(TopoDS::Wire(expWire.Current()));			
	}
}*/