/*#include <boost/python.hpp>
using namespace boost::python;
*/
#include <zencad/base.h>
#include <zencad/cache.h>
#include <zencad/topo.h>
#include <zencad/solid.h>
#include <zencad/wire.h>
#include <zencad/face.h>
#include <zencad/boolops.h>
#include <zencad/trans.h>
#include <zencad/stl.h>
#include <zencad/widget.h>

#include <zencad/math3.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
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

#define DEF_EXPLORER_OPERATIONS(TYPE) 				\
.def("wires", &TYPE::wires)							\
.def("vertexs", &TYPE::vertexs)				


PYBIND11_MODULE(zenlib, m) {
	py::class_<ZenCadObject, std::shared_ptr<ZenCadObject>>(m, "ZenCadObject")
		.def("get_hash1", &ZenCadObject::get_hash1)
		.def("get_hash2", &ZenCadObject::get_hash2)
		.def("get_hash_base64", &ZenCadObject::get_hash_base64)		
	;
	py::class_<ZenShape, ZenCadObject, std::shared_ptr<ZenShape>>(m, "ZenShape")
		.def("dump", &ZenShape::dump_binary);

	py::class_<ZenVertex, ZenShape, std::shared_ptr<ZenVertex>>(m, "ZenVertex")
		DEF_TRANSFORM_OPERATIONS(ZenVertex)
		DEF_EXPLORER_OPERATIONS(ZenVertex)
		.def(py::init<double, double, double>())
	;

	///SOLIDS
	py::class_<ZenSolid, ZenShape, std::shared_ptr<ZenSolid>>(m, "ZenSolid")
		DEF_TRANSFORM_OPERATIONS(ZenSolid)
		DEF_EXPLORER_OPERATIONS(ZenSolid)
		.def(py::self + py::self)
		.def(py::self - py::self)
		.def(py::self ^ py::self)
	;
	m.def("solid_load", zen_load<ZenSolid>);

	py::class_<ZenBox, ZenSolid, std::shared_ptr<ZenBox>>(m, "solid_box")
		.def(py::init<double, double, double>())
		.def(py::init<double, double, double, py::kwargs>());


	py::class_<ZenSphere, ZenSolid, std::shared_ptr<ZenSphere>>(m, "solid_sphere")
		.def(py::init<double>());


	py::class_<ZenCylinder, ZenSolid, std::shared_ptr<ZenCylinder>>(m, "solid_cylinder")
		.def(py::init<double, double>());

	py::class_<ZenTorus, ZenSolid, std::shared_ptr<ZenTorus>>(m, "solid_torus")
		.def(py::init<double, double>());

	py::class_<ZenWedge, ZenSolid, std::shared_ptr<ZenWedge>>(m, "solid_wedge")
		.def(py::init<double, double, double, double>());
	
	py::class_<ZenLinearExtrude, ZenSolid, std::shared_ptr<ZenLinearExtrude>>(m, "solid_linear_extrude")
		.def(py::init<std::shared_ptr<ZenFace>, double>())
		.def(py::init<std::shared_ptr<ZenFace>, ZenVector3>());

	py::class_<ZenLoft, ZenSolid, std::shared_ptr<ZenLoft>>(m, "solid_loft")
		.def(py::init<py::list>());

	py::class_<ZenPipe, ZenSolid, std::shared_ptr<ZenPipe>>(m, "solid_pipe")
		.def(py::init<std::shared_ptr<ZenWire>, std::shared_ptr<ZenShape>>());
	
	///EDGES
	py::class_<ZenEdge, ZenShape, std::shared_ptr<ZenEdge>>(m, "ZenEdge")
		DEF_TRANSFORM_OPERATIONS(ZenEdge)
		DEF_EXPLORER_OPERATIONS(ZenEdge)
		.def("face", &ZenEdge::make_face)
	;

	///WIRES
	py::class_<ZenWire, ZenShape, std::shared_ptr<ZenWire>>(m, "ZenWire")
		DEF_TRANSFORM_OPERATIONS(ZenWire)
		DEF_EXPLORER_OPERATIONS(ZenWire)
		.def("face", &ZenWire::make_face)
	;

	py::class_<ZenSegment, ZenWire, std::shared_ptr<ZenSegment>>(m, "wire_segment")
		.def(py::init<ZenPoint3, ZenPoint3>());

	py::class_<ZenWireCircle, ZenWire, std::shared_ptr<ZenWireCircle>>(m, "wire_circle")
		.def(py::init<double, py::kwargs>(), py::arg("r"));

	py::class_<ZenCircleArcByPoints, ZenWire, std::shared_ptr<ZenCircleArcByPoints>>(m, "wire_circle_arc_by_points")
		.def(py::init<ZenPoint3, ZenPoint3, ZenPoint3>());

	py::class_<ZenPolySegment, ZenWire, std::shared_ptr<ZenPolySegment>>(m, "wire_polysegment")
		.def(py::init<py::list>())
		.def(py::init<py::list, py::kwargs>())
	;


	py::class_<ZenWireComplex, ZenWire, std::shared_ptr<ZenWireComplex>>(m, "wire_complex")
		.def(py::init<py::list>())
	;


	//py::class_<ZenWiresFromFace, ZenWire, std::shared_ptr<ZenWiresFromFace>>(m, "wires_from_face")
	//	.def(py::init<std::shared_ptr<std::shared_ptr<ZenFace>>>())
	//;
		
	///FACE	
	py::class_<ZenFace, ZenShape, std::shared_ptr<ZenFace>>(m, "ZenFace")
		DEF_TRANSFORM_OPERATIONS(ZenFace)
		DEF_EXPLORER_OPERATIONS(ZenFace)
		.def(py::self + py::self)
		.def(py::self - py::self)
		.def(py::self ^ py::self)
		.def("fillet", &ZenFace::fillet)
		//.def("wires", &ZenFace::wires)
	;

	py::class_<ZenPolygon, ZenFace, std::shared_ptr<ZenPolygon>>(m, "face_polygon")
		.def(py::init<py::list>());

	py::class_<ZenFilletFace, ZenFace, std::shared_ptr<ZenFilletFace>>(m, "face_fillet")
		.def(py::init<std::shared_ptr<ZenFace>, int>());
		
	py::class_<ZenCircle, ZenFace, std::shared_ptr<ZenCircle>>(m, "face_circle")
		.def(py::init<double>());

	///TRANS
	py::class_<ZenTransform, std::shared_ptr<ZenTransform>>(m, "ZenTransform");
	m.def("trans_translate", trans_translate);

	///COMPAT
	m.def("make_stl", make_stl);

	///CACHE
	m.def("cache_enable", zencache_enable);
	m.def("cache_disable", zencache_disable);
	m.def("cache_is_enabled", zencache_is_enabled);

	///VIEW
	m.def("display", display);
	m.def("show", show);

	py::class_<ZenDirection3>(m, "direction3").def(py::init<double,double,double>());
	py::class_<ZenVector3>(m, "vector3").def(py::init<double,double,double>());
	py::class_<ZenPoint3>(m, "point3")
		.def(py::init<double,double,double>())
		.def(py::init<double,double>());

	py::class_<ZenShapeExplorer<ZenWire>, std::shared_ptr<ZenShapeExplorer<ZenWire>>>(m, "ZenShapeExplorer<ZenWire>")
		.def("__len__", &ZenShapeExplorer<ZenWire>::size)
		.def("__getitem__", &ZenShapeExplorer<ZenWire>::getitem)
	;	

	py::class_<ZenShapeExplorer<ZenVertex>, std::shared_ptr<ZenShapeExplorer<ZenVertex>>>(m, "ZenShapeExplorer<ZenVertex>")
		.def("__len__", &ZenShapeExplorer<ZenVertex>::size)
		.def("__getitem__", &ZenShapeExplorer<ZenVertex>::getitem)
	;	

	//py::class_<ZenShapeExplorer<ZenFace>, std::shared_ptr<ZenShapeExplorer<ZenFace>>>(m, "ZenShapeExplorer<ZenFace>");
	//;

	//py::class_<ZenShapeExplorer<ZenSolid>, std::shared_ptr<ZenShapeExplorer<ZenSolid>>>(m, "ZenShapeExplorer<ZenSolid>");
	//;
}
