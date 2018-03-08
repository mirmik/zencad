#include <QtWidgets/QApplication>
#include <DzenWidget.h>

int main(int argc, char *argv[]) {
    QApplication a(argc, argv);

    DzenWidget w;
    w.show();
    
    return a.exec();
}
