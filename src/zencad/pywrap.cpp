#include <servoce/servoce.h>
#include <servoce/display.h>
#include <servoce/except.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#define DEF_TRANSFORM_OPERATIONS(TYPE) 				\
.def("transform", &TYPE::transform)				\
.def("translate", &TYPE::translate)				\
.def("up", &TYPE::up)							\
.def("down", &TYPE::down)						\
.def("right", &TYPE::right)						\
.def("left", &TYPE::left)						\
.def("forw", &TYPE::forw)						\
.def("back", &TYPE::back)						\
.def("rotateX", &TYPE::rotateX)					\
.def("rotateY", &TYPE::rotateY)					\
.def("rotateZ", &TYPE::rotateZ)					\
.def("mirrorX", &TYPE::mirrorX)					\
.def("mirrorY", &TYPE::mirrorY)					\
.def("mirrorZ", &TYPE::mirrorZ)					\
.def("mirrorXY", &TYPE::mirrorXY)				\
.def("mirrorYZ", &TYPE::mirrorYZ)				\
.def("mirrorXZ", &TYPE::mirrorXZ)				
/*
#define DEF_EXPLORER_OPERATIONS(TYPE) 				\
.def("wires", &TYPE::wires)							\
.def("vertexs", &TYPE::vertexs)				

*/

PYBIND11_MODULE(zenlib, m) {
	py::register_exception<servoce::RuntimeException>(m, "ServoceRuntimeException");

	py::class_<servoce::point3>(m, "point3")
	.def(py::init<double,double,double>());
	py::class_<servoce::vector3>(m, "vector3")
	.def(py::init<double,double,double>());

	py::class_<servoce::shape>(m, "Shape");

	py::class_<servoce::solid, servoce::shape>(m, "Solid")
	DEF_TRANSFORM_OPERATIONS(servoce::solid);
	m.def("make_box", servoce::prim3d::make_box, py::arg("x"), py::arg("y"), py::arg("z"), py::arg("center") = false);
	m.def("make_sphere", 	servoce::prim3d::make_sphere);
	m.def("make_cylinder", 	servoce::prim3d::make_cylinder);
	m.def("make_cone", 		servoce::prim3d::make_cone);
	m.def("make_torus", 	servoce::prim3d::make_torus);

	py::class_<servoce::face, servoce::shape>(m, "Face")
	DEF_TRANSFORM_OPERATIONS(servoce::face);

	py::class_<servoce::wire, servoce::shape>(m, "Wire")
	DEF_TRANSFORM_OPERATIONS(servoce::wire);
	m.def("make_segment", servoce::curve::make_segment);
	m.def("make_polysegment", servoce::curve::make_polysegment, py::arg("pnts"), py::arg("closed") = false);
	//m.def("make_interpolate", servoce::curve::make_interpolate);

	py::class_<servoce::sweep_solid, servoce::shape>(m, "Sweep");
	
	py::class_<servoce::scene>(m, "Scene")
	.def(py::init<>())
	.def("add", &servoce::scene::add);

	m.def("display_scene", 	servoce::display);
}
