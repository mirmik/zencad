//#include <boost/python.hpp>
//using namespace boost::python;
#include <pybind11/pybind11.h>

#include <QtWidgets/QApplication>
#include <dzencad/DzenWidget.h>

#include <dzencad/topo.h>
#include <dzencad/widget.h>
#include <AIS_Shape.hxx>

QApplication* a = nullptr;
DzenWidget* w = nullptr;
int argc = 0;

void display(std::shared_ptr<DzenShape> ptr) {
    //gxx::println("display");
	if (!a) {
		a = new QApplication(argc, nullptr);
    	w = new DzenWidget;
    }

    //gxx::println("prepare");
    ptr->prepare();
    //gxx::println("link");
	w->display->display_on_init_list.push_back(ptr->native());
}

void display_native(const TopoDS_Shape& shp) {
    if (!a) {
        a = new QApplication(argc, nullptr);
        w = new DzenWidget;
    }

    w->display->display_on_init_list.push_back(shp);
}

void show() {
	QLocale curLocale(QLocale("en_EN"));
    QLocale::setDefault(curLocale);

    if (a == nullptr) {
		int argc = 0;
    	a = new QApplication(argc, nullptr);
    	w = new DzenWidget;
    }

    w->show();
	a->exec();
}