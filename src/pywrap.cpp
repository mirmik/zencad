#include <servoce/servoce.h>
#include <servoce/display.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#define DEF_TRANSFORM_OPERATIONS(TYPE) 				\
.def("transform", &TYPE::transform)				\
.def("translate", (TYPE(TYPE::*)(double, double, double))&TYPE::transform)				\
.def("translate", (TYPE(TYPE::*)(double, double))&TYPE::translate)				\
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
	//py::register_exception<servoce::RuntimeException>(m, "ServoceRuntimeException");

	py::class_<servoce::point3>(m, "point3")
		DEF_TRANSFORM_OPERATIONS(servoce::point3)
		.def(py::init<double,double,double>())
		.def(py::init<double,double>())
		.def_readwrite("x", &servoce::point3::x)
		.def_readwrite("y", &servoce::point3::y)
		.def_readwrite("z", &servoce::point3::z)
	;
	
	py::class_<servoce::vector3>(m, "vector3")
		DEF_TRANSFORM_OPERATIONS(servoce::vector3)
		.def(py::init<double,double,double>())
		.def(py::init<double,double>())
		.def_readwrite("x", &servoce::vector3::x)
		.def_readwrite("y", &servoce::vector3::y)
		.def_readwrite("z", &servoce::vector3::z)
	;

	py::class_<servoce::shape>(m, "Shape");

	py::class_<servoce::solid, servoce::shape>(m, "Solid")
		DEF_TRANSFORM_OPERATIONS(servoce::solid)
		.def(py::self + py::self)
		.def(py::self - py::self)
		.def(py::self ^ py::self)
	;

	m.def("make_box", servoce::prim3d::make_box, py::arg("x"), py::arg("y"), py::arg("z"), py::arg("center") = false);
	m.def("make_sphere", 	servoce::prim3d::make_sphere, py::arg("r"));
	m.def("make_cylinder", 	servoce::prim3d::make_cylinder, py::arg("r"), py::arg("h"), py::arg("center") = false);
	m.def("make_cone", 		servoce::prim3d::make_cone, py::arg("r1"), py::arg("r2"), py::arg("h"), py::arg("center") = false);
	m.def("make_torus", 	servoce::prim3d::make_torus, py::arg("r1"), py::arg("r2"));

	m.def("make_linear_extrude", 	servoce::sweep3d::make_linear_extrude, py::arg("shp"), py::arg("vec"));
	m.def("make_pipe", 				servoce::sweep3d::make_pipe, py::arg("prof"), py::arg("path"));

	py::class_<servoce::face, servoce::shape>(m, "Face")
		DEF_TRANSFORM_OPERATIONS(servoce::face)
		.def("fillet", &servoce::face::fillet, py::arg("r"), py::arg("nums"))
		//.def(py::self + py::self)
		//.def(py::self - py::self)
		//.def(py::self ^ py::self)
	;
	m.def("make_circle", 	servoce::prim2d::make_circle, py::arg("r"));
	m.def("make_ngon", 		servoce::prim2d::make_ngon, py::arg("r"), py::arg("n"));
	m.def("make_square", 	servoce::prim2d::make_square, py::arg("a"), py::arg("center") = false);
	m.def("make_rectangle", servoce::prim2d::make_rectangle, py::arg("a"), py::arg("b"), py::arg("center") = false);
	m.def("make_polygon", 	(servoce::face(*)(const std::vector<servoce::point3>&))&servoce::prim2d::make_polygon, py::arg("pnts"));
	m.def("make_sweep", 	servoce::sweep2d::make_sweep, py::arg("prof"), py::arg("path"));

	py::class_<servoce::wire, servoce::shape>(m, "Wire")
		DEF_TRANSFORM_OPERATIONS(servoce::wire)
		.def("face", &servoce::wire::to_face)
	;
	
	m.def("make_segment", servoce::curve::make_segment);
	m.def("make_polysegment", servoce::curve::make_polysegment, py::arg("pnts"), py::arg("closed") = false);
	m.def("make_interpolate", (servoce::wire(*)(const std::vector<servoce::point3>&, const std::vector<servoce::vector3>&, bool))&servoce::curve::make_interpolate, py::arg("pnts"), py::arg("tang"), py::arg("closed") = false);
	m.def("make_interpolate", (servoce::wire(*)(const std::vector<servoce::point3>&, const bool))&servoce::curve::make_interpolate, py::arg("pnts"), py::arg("closed") = false);
	m.def("make_helix", servoce::curve::make_helix, py::arg("pitch"), py::arg("height"), py::arg("radius"), py::arg("angle") = 0, py::arg("leftHanded") = false, py::arg("newStyle") = true);
	m.def("make_long_helix", servoce::curve::make_long_helix, py::arg("pitch"), py::arg("height"), py::arg("radius"), py::arg("angle") = 0, py::arg("leftHanded") = false);
	m.def("make_complex_wire", servoce::curve::make_complex_wire, py::arg("wires"));

	py::class_<servoce::sweep_solid, servoce::solid>(m, "SolidSweep");
	py::class_<servoce::sweep_face, servoce::face>(m, "FaceSweep");
	
	py::class_<servoce::scene>(m, "Scene")
		.def(py::init<>())
		.def("add", &servoce::scene::add)
	;

	m.def("make_union", (servoce::solid(*)(const std::vector<const servoce::solid*>&))&servoce::boolops::make_union);
	m.def("make_difference", (servoce::solid(*)(const std::vector<const servoce::solid*>&))&servoce::boolops::make_difference);
	m.def("make_intersect", (servoce::solid(*)(const std::vector<const servoce::solid*>&))&servoce::boolops::make_intersect);


	m.def("display_scene", 	servoce::display);
}
