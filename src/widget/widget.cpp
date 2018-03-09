#include <boost/python.hpp>
using namespace boost::python;

#include <QtWidgets/QApplication>
#include <DzenWidget.h>

#include <dzencad/base.h>

#include <AIS_Shape.hxx>

QApplication* a = nullptr;
DzenWidget* w = nullptr;
int argc = 0;

void display(std::shared_ptr<DzenShape> ptr) {
	if (!a) {
		a = new QApplication(argc, nullptr);
    	w = new DzenWidget;
    }

    ptr->prepare();
	w->display->display_on_init_list.push_back(ptr);
}

void show() {
	if (a == nullptr) {
		int argc = 0;
    	a = new QApplication(argc, nullptr);
    	w = new DzenWidget;
    }

    w->show();
	a->exec();
}

BOOST_PYTHON_MODULE(widget) {
    def("display", display, args("shape"), "display's docstring");
    def("show", show);
}