/*#include <boost/python.hpp>
using namespace boost::python;
*/
#include <zencad/base.h>
#include <zencad/cache.h>
#include <zencad/topo.h>
#include <zencad/solid.h>
#include <zencad/wire.h>
#include <zencad/boolops.h>
#include <zencad/trans.h>
#include <zencad/stl.h>
#include <zencad/widget.h>

#include <zencad/math3.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
namespace py = pybind11;

PYBIND11_MODULE(zenlib, m) {
	py::class_<ZenCadObject, std::shared_ptr<ZenCadObject>>(m, "ZenCadObject")
		.def("get_hash1", &ZenCadObject::get_hash1)
		.def("get_hash2", &ZenCadObject::get_hash2)
		.def("get_hash_base64", &ZenCadObject::get_hash_base64)		
	;
	py::class_<ZenShape, ZenCadObject, std::shared_ptr<ZenShape>>(m, "ZenShape")
		.def("dump", &ZenShape::dump_binary)
		//.def("load", &ZenShape::load_binary)
	;

	//py::class_<ZenShape, std::shared_ptr<ZenShape>>(m, "ZenShape")
	//    .def("transform", &ZenShape::transform)
	//    
	//    .def("translate", &ZenShape::translate)
	//    .def("up", &ZenShape::up)
	//    .def("down", &ZenShape::down)
	//    .def("right", &ZenShape::right)
	//    .def("left", &ZenShape::left)
	//    .def("forw", &ZenShape::forw)
	//    .def("back", &ZenShape::back)
//
	//    .def("rotateX", &ZenShape::rotateX)
	//    .def("rotateY", &ZenShape::rotateY)
	//    .def("rotateZ", &ZenShape::rotateZ)
//
	//    .def("mirrorX", &ZenShape::mirrorX)
	//    .def("mirrorY", &ZenShape::mirrorY)
	//    .def("mirrorZ", &ZenShape::mirrorZ)
//
	//    .def("mirrorXY", &ZenShape::mirrorXY)
	//    .def("mirrorYZ", &ZenShape::mirrorYZ)
	//    .def("mirrorXZ", &ZenShape::mirrorXZ)
//
	//  	.def(py::self + py::self)
	//	.def(py::self - py::self)
	//	.def(py::self ^ py::self)
	//;

	py::class_<ZenSolid, ZenShape, std::shared_ptr<ZenSolid>>(m, "ZenSolid")
		.def("transform", &ZenSolid::transform)
		
		.def("translate", &ZenSolid::translate)
		.def("up", &ZenSolid::up)
		.def("down", &ZenSolid::down)
		.def("right", &ZenSolid::right)
		.def("left", &ZenSolid::left)
		.def("forw", &ZenSolid::forw)
		.def("back", &ZenSolid::back)

		.def("rotateX", &ZenSolid::rotateX)
		.def("rotateY", &ZenSolid::rotateY)
		.def("rotateZ", &ZenSolid::rotateZ)

		.def("mirrorX", &ZenSolid::mirrorX)
		.def("mirrorY", &ZenSolid::mirrorY)
		.def("mirrorZ", &ZenSolid::mirrorZ)

		.def("mirrorXY", &ZenSolid::mirrorXY)
		.def("mirrorYZ", &ZenSolid::mirrorYZ)
		.def("mirrorXZ", &ZenSolid::mirrorXZ)
		
		.def(py::self + py::self)
		.def(py::self - py::self)
		.def(py::self ^ py::self)
	;
	m.def("solid_load", zen_load<ZenSolid>);

	py::class_<ZenWire, ZenShape, std::shared_ptr<ZenWire>>(m, "ZenWire")
		.def("face", &ZenWire::make_face);

	py::class_<ZenEdge, ZenShape, std::shared_ptr<ZenEdge>>(m, "ZenEdge");

	py::class_<ZenFace, ZenShape, std::shared_ptr<ZenFace>>(m, "ZenFace");
	
	py::class_<ZenTransform, std::shared_ptr<ZenTransform>>(m, "ZenTransform");

	//class_<ZenUnion, std::shared_ptr<ZenUnion> , boost::noncopyable >("ZenUnion", init<std::shared_ptr<ZenShape>, std::shared_ptr<ZenShape>>());
	//class_<ZenBox, std::shared_ptr<ZenBox> , boost::noncopyable >("box", init<double, double, double>());
	
	//m.def("solid_box", solid_box);
	//m.def("solid_sphere", solid_sphere);
	//m.def("solid_cylinder", solid_cylinder);
	//m.def("solid_torus", solid_torus);

	py::class_<ZenBox, ZenSolid, std::shared_ptr<ZenBox>>(m, "solid_box")
		.def(py::init<double, double, double>())
		.def(py::init<double, double, double, py::kwargs>());


	py::class_<ZenSphere, ZenSolid, std::shared_ptr<ZenSphere>>(m, "solid_sphere")
		.def(py::init<double>());


	py::class_<ZenCylinder, ZenSolid, std::shared_ptr<ZenCylinder>>(m, "solid_cylinder")
		.def(py::init<double, double>());


	py::class_<ZenTorus, ZenSolid, std::shared_ptr<ZenTorus>>(m, "solid_torus")
		.def(py::init<double, double>());
	
	//m.def("wire_segment", wire_segment);
	//m.def("wire_polysegment", wire_polysegment);

	//m.def("boolops_union", boolops_union);
	py::class_<ZenSegment, ZenEdge, std::shared_ptr<ZenSegment>>(m, "edge_segment")
		.def(py::init<ZenPoint3, ZenPoint3>());

	py::class_<ZenPolySegment, ZenWire, std::shared_ptr<ZenPolySegment>>(m, "wire_polysegment")
		.def(py::init<py::list>())
		.def(py::init<py::list, py::kwargs>());


	m.def("trans_translate", trans_translate);

	m.def("make_stl", make_stl);

	m.def("cache_enable", zencache_enable);
	m.def("cache_disable", zencache_disable);
	m.def("cache_is_enabled", zencache_is_enabled);

	m.def("display", display);
	m.def("show", show);

	py::class_<ZenDirection3>(m, "direction3").def(py::init<double,double,double>());
	py::class_<ZenVector3>(m, "vector3").def(py::init<double,double,double>());
	py::class_<ZenPoint3>(m, "point3").def(py::init<double,double,double>());
	
}
