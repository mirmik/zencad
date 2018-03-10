/*#include <boost/python.hpp>
using namespace boost::python;
*/
#include <dzencad/base.h>
#include <dzencad/cache.h>
#include <dzencad/topo.h>
#include <dzencad/solid.h>
#include <dzencad/boolops.h>
#include <dzencad/trans.h>
#include <dzencad/stl.h>
#include <dzencad/widget.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
namespace py = pybind11;

PYBIND11_MODULE(dzenlib, m) {
	py::class_<DzenCadObject, std::shared_ptr<DzenCadObject>>(m, "DzenCadObject");
	py::class_<DzenShape, std::shared_ptr<DzenShape>>(m, "DzenShape")
        .def("transform", &DzenShape::transform)
	    
	    .def("translate", &DzenShape::translate)
	    .def("up", &DzenShape::up)
	    .def("down", &DzenShape::down)
	    .def("right", &DzenShape::right)
	    .def("left", &DzenShape::left)
	    .def("forw", &DzenShape::forw)
	    .def("back", &DzenShape::back)

	    .def("rotateX", &DzenShape::rotateX)
	    .def("rotateY", &DzenShape::rotateY)
	    .def("rotateZ", &DzenShape::rotateZ)

    	//.def(py::self + py::other<std::shared_ptr<DzenShape>>())
    	//.def(py::self - py::other<std::shared_ptr<DzenShape>>())
    	//.def(py::self ^ py::other<std::shared_ptr<DzenShape>>())

    	.def(py::self + py::self)
    	.def(py::self - py::self)
    	.def(py::self ^ py::self)
    ;
	
	py::class_<DzenTransform, std::shared_ptr<DzenTransform>>(m, "DzenTransform");

	//class_<DzenUnion, std::shared_ptr<DzenUnion> , boost::noncopyable >("DzenUnion", init<std::shared_ptr<DzenShape>, std::shared_ptr<DzenShape>>());
	//class_<DzenBox, std::shared_ptr<DzenBox> , boost::noncopyable >("box", init<double, double, double>());
	
	m.def("solid_box", solid_box);
	m.def("solid_sphere", solid_sphere);
	m.def("solid_cylinder", solid_cylinder);
	m.def("solid_torus", solid_torus);

	m.def("boolops_union", boolops_union);

	m.def("trans_translate", trans_translate);

	m.def("make_stl", make_stl);

	m.def("enable_cache", dzencache_enable);
	m.def("disable_cache", dzencache_disable);


    m.def("display", display);
    m.def("show", show);
}
