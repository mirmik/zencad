/*#include <boost/python.hpp>
using namespace boost::python;
*/
#include <dzencad/base.h>
#include <dzencad/cache.h>
#include <dzencad/topo.h>
#include <dzencad/solid.h>
#include <dzencad/wire.h>
#include <dzencad/boolops.h>
#include <dzencad/trans.h>
#include <dzencad/stl.h>
#include <dzencad/widget.h>

#include <dzencad/math3.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
namespace py = pybind11;

PYBIND11_MODULE(dzenlib, m) {
	py::class_<DzenCadObject, std::shared_ptr<DzenCadObject>>(m, "DzenCadObject");
	py::class_<DzenShape, DzenCadObject, std::shared_ptr<DzenShape>>(m, "DzenShape");
	
	//py::class_<DzenShape, std::shared_ptr<DzenShape>>(m, "DzenShape")
	//    .def("transform", &DzenShape::transform)
	//    
	//    .def("translate", &DzenShape::translate)
	//    .def("up", &DzenShape::up)
	//    .def("down", &DzenShape::down)
	//    .def("right", &DzenShape::right)
	//    .def("left", &DzenShape::left)
	//    .def("forw", &DzenShape::forw)
	//    .def("back", &DzenShape::back)
//
	//    .def("rotateX", &DzenShape::rotateX)
	//    .def("rotateY", &DzenShape::rotateY)
	//    .def("rotateZ", &DzenShape::rotateZ)
//
	//    .def("mirrorX", &DzenShape::mirrorX)
	//    .def("mirrorY", &DzenShape::mirrorY)
	//    .def("mirrorZ", &DzenShape::mirrorZ)
//
	//    .def("mirrorXY", &DzenShape::mirrorXY)
	//    .def("mirrorYZ", &DzenShape::mirrorYZ)
	//    .def("mirrorXZ", &DzenShape::mirrorXZ)
//
	//  	.def(py::self + py::self)
	//	.def(py::self - py::self)
	//	.def(py::self ^ py::self)
	//;

	py::class_<DzenSolid, DzenShape, std::shared_ptr<DzenSolid>>(m, "DzenSolid")
		.def("transform", &DzenSolid::transform)
		
		.def("translate", &DzenSolid::translate)
		.def("up", &DzenSolid::up)
		.def("down", &DzenSolid::down)
		.def("right", &DzenSolid::right)
		.def("left", &DzenSolid::left)
		.def("forw", &DzenSolid::forw)
		.def("back", &DzenSolid::back)

		.def("rotateX", &DzenSolid::rotateX)
		.def("rotateY", &DzenSolid::rotateY)
		.def("rotateZ", &DzenSolid::rotateZ)

		.def("mirrorX", &DzenSolid::mirrorX)
		.def("mirrorY", &DzenSolid::mirrorY)
		.def("mirrorZ", &DzenSolid::mirrorZ)

		.def("mirrorXY", &DzenSolid::mirrorXY)
		.def("mirrorYZ", &DzenSolid::mirrorYZ)
		.def("mirrorXZ", &DzenSolid::mirrorXZ)
		
		.def(py::self + py::self)
		.def(py::self - py::self)
		.def(py::self ^ py::self)
	;


	py::class_<DzenWire, DzenShape, std::shared_ptr<DzenWire>>(m, "DzenWire")
		.def("face", &DzenWire::make_face);

	py::class_<DzenEdge, DzenShape, std::shared_ptr<DzenEdge>>(m, "DzenEdge");

	py::class_<DzenFace, DzenShape, std::shared_ptr<DzenFace>>(m, "DzenFace");
	
	py::class_<DzenTransform, std::shared_ptr<DzenTransform>>(m, "DzenTransform");

	//class_<DzenUnion, std::shared_ptr<DzenUnion> , boost::noncopyable >("DzenUnion", init<std::shared_ptr<DzenShape>, std::shared_ptr<DzenShape>>());
	//class_<DzenBox, std::shared_ptr<DzenBox> , boost::noncopyable >("box", init<double, double, double>());
	
	//m.def("solid_box", solid_box);
	//m.def("solid_sphere", solid_sphere);
	//m.def("solid_cylinder", solid_cylinder);
	//m.def("solid_torus", solid_torus);

	py::class_<DzenBox, DzenSolid, std::shared_ptr<DzenBox>>(m, "solid_box")
		.def(py::init<double, double, double>())
		.def(py::init<double, double, double, py::kwargs>());


	py::class_<DzenSphere, DzenSolid, std::shared_ptr<DzenSphere>>(m, "solid_sphere")
		.def(py::init<double>());


	py::class_<DzenCylinder, DzenSolid, std::shared_ptr<DzenCylinder>>(m, "solid_cylinder")
		.def(py::init<double, double>());


	py::class_<DzenTorus, DzenSolid, std::shared_ptr<DzenTorus>>(m, "solid_torus")
		.def(py::init<double, double>());
	
	//m.def("wire_segment", wire_segment);
	//m.def("wire_polysegment", wire_polysegment);

	//m.def("boolops_union", boolops_union);
	py::class_<DzenSegment, DzenEdge, std::shared_ptr<DzenSegment>>(m, "edge_segment")
		.def(py::init<DzenPoint3, DzenPoint3>());

	py::class_<DzenPolySegment, DzenWire, std::shared_ptr<DzenPolySegment>>(m, "wire_polysegment")
		.def(py::init<py::list>())
		.def(py::init<py::list, py::kwargs>());


	m.def("trans_translate", trans_translate);

	m.def("make_stl", make_stl);

	m.def("enable_cache", dzencache_enable);
	m.def("disable_cache", dzencache_disable);


	m.def("display", display);
	m.def("show", show);

	py::class_<DzenDirection3>(m, "direction3").def(py::init<double,double,double>());
	py::class_<DzenVector3>(m, "vector3").def(py::init<double,double,double>());
	py::class_<DzenPoint3>(m, "point3").def(py::init<double,double,double>());
	
}
