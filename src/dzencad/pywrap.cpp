#include <boost/python.hpp>
using namespace boost::python;

#include <dzencad/base.h>
#include <dzencad/cache.h>
#include <dzencad/topo.h>
#include <dzencad/solid.h>
#include <dzencad/boolops.h>
#include <dzencad/trans.h>
#include <dzencad/stl.h>

BOOST_PYTHON_MODULE(dzenlib) {
	class_<DzenCadObject, std::shared_ptr<DzenCadObject> , boost::noncopyable >("DzenCadObject");
	class_<DzenShape, std::shared_ptr<DzenShape> , boost::noncopyable >("DzenShape")
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

    	.def(self + other<std::shared_ptr<DzenShape>>())
    	.def(self - other<std::shared_ptr<DzenShape>>())
    	.def(self ^ other<std::shared_ptr<DzenShape>>())
    ;
	
	class_<DzenTransform, std::shared_ptr<DzenTransform> , boost::noncopyable >("DzenTransform");

	//class_<DzenUnion, std::shared_ptr<DzenUnion> , boost::noncopyable >("DzenUnion", init<std::shared_ptr<DzenShape>, std::shared_ptr<DzenShape>>());
	//class_<DzenBox, std::shared_ptr<DzenBox> , boost::noncopyable >("box", init<double, double, double>());
	
	def("solid_box", solid_box);
	def("solid_sphere", solid_sphere);
	def("solid_cylinder", solid_cylinder);
	def("solid_torus", solid_torus);

	def("boolops_union", boolops_union);

	def("trans_translate", trans_translate);

	def("make_stl", make_stl);

	def("enable_cache", dzencache_enable);
	def("disable_cache", dzencache_disable);
}