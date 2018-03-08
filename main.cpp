#include "occQt.h"


#include <QtCore/QVariant>
#include <QtWidgets/QAction>
#include <QtWidgets/QApplication>
#include <QtWidgets/QButtonGroup>
#include <QtWidgets/QHeaderView>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QMenuBar>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QWidget>
//#include <QApplication>

int main(int argc, char *argv[]) {
    QApplication a(argc, argv);

    occQt w;
    w.show();
    
    return a.exec();
}
