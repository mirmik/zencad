#include <dzencad/DzenWidget.h>
#include <QtWidgets/QMessageBox>
#include <QtWidgets/QFileDialog>
#include <QtWidgets/QInputDialog>
#include <QtCore/QDebug>

// occ header files.
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <StlAPI_Writer.hxx>

#include <V3d_View.hxx>
#include <AIS_Shape.hxx>

//#include <gxx/print.h>

DzenWidget::DzenWidget(QWidget* parent) : QMainWindow(parent) {
    display = new DisplayWidget(this);
    
    createActions();
    createMenus();

    setCentralWidget(display);
    resize(640, 480);
}

void DzenWidget::createActions() {
    mExitAction = new QAction(tr("Exit"), this);
    mExitAction->setShortcut(tr("Ctrl+Q"));
    mExitAction->setStatusTip(tr("Exit the application"));
    connect(mExitAction, SIGNAL(triggered()), this, SLOT(close()));

    mStlExport = new QAction(tr("Export STL..."), this);
    mStlExport->setStatusTip(tr("Export file with external STL-Mesh format"));
    connect(mStlExport, SIGNAL(triggered()), this, SLOT(export_stl()));

    mAboutAction = new QAction(tr("About"), this);
    mAboutAction->setStatusTip(tr("About the application"));
    connect(mAboutAction, SIGNAL(triggered()), this, SLOT(about()));
}

void DzenWidget::createMenus() {
    mFileMenu = menuBar()->addMenu(tr("&File"));
    mFileMenu->addAction(mStlExport);
    mFileMenu->addSeparator();
    mFileMenu->addAction(mExitAction);

    mHelpMenu = menuBar()->addMenu(tr("&Help"));
    mHelpMenu->addAction(mAboutAction);
}

void DzenWidget::createToolbars() {

}

void DzenWidget::about() {
    QMessageBox::about(this, tr("About DzenWidget"),
        tr("<h2>DzenWidget</h2>"
        "<p>Author: mirmik(mirmikns@yandex.ru) 2018"
        "<p>DzenCad shower."
        "<p>Based on occQt demo applicaton."));
}


void DzenWidget::export_stl() {
    //gxx::println("export_stl");
    bool ok;
    
    QFileDialog fileDialog(this, "Choose file to export");
    fileDialog.setNameFilter("STL-Mesh (*.stl)");
    fileDialog.setDefaultSuffix(".stl");
    ok = fileDialog.exec();

    if (!ok) return;
    QString path = fileDialog.selectedFiles().first();

    QInputDialog *inputDialog = new QInputDialog();
    inputDialog->setTextValue("Test"); // has no effect
    
    double d = QInputDialog::getDouble(this, tr("QInputDialog::getDouble()"),
                                       tr("Amount:"), 0.01, 0, 10, 5, &ok);

    if (display->display_on_init_list.size() != 1) {
        exit(1);
        //gxx::panic("TODO");
    } 

    StlAPI_Writer stl_writer;
    stl_writer.SetDeflection(d);
    stl_writer.RelativeMode() = false;
    stl_writer.Write(display->display_on_init_list[0]->shape(), path.toStdString().c_str());
}

/*void DzenWidget::makeBox() {
    TopoDS_Shape aTopoBox = BRepPrimAPI_MakeBox(3.0, 4.0, 5.0).Shape();
    Handle(AIS_Shape) anAisBox = new AIS_Shape(aTopoBox);

    anAisBox->SetColor(Quantity_NOC_AZURE);

    display->getContext()->Display(anAisBox);
}


void DzenWidget::makeCone()
{
    gp_Ax2 anAxis;
    anAxis.SetLocation(gp_Pnt(0.0, 10.0, 0.0));

    TopoDS_Shape aTopoReducer = BRepPrimAPI_MakeCone(anAxis, 3.0, 1.5, 5.0).Shape();
    Handle(AIS_Shape) anAisReducer = new AIS_Shape(aTopoReducer);

    anAisReducer->SetColor(Quantity_NOC_BISQUE);

    anAxis.SetLocation(gp_Pnt(8.0, 10.0, 0.0));
    TopoDS_Shape aTopoCone = BRepPrimAPI_MakeCone(anAxis, 3.0, 0.0, 5.0).Shape();
    Handle(AIS_Shape) anAisCone = new AIS_Shape(aTopoCone);

    anAisCone->SetColor(Quantity_NOC_CHOCOLATE);

    display->getContext()->Display(anAisReducer);
    display->getContext()->Display(anAisCone);
}

void DzenWidget::makeSphere()
{
    gp_Ax2 anAxis;
    anAxis.SetLocation(gp_Pnt(0.0, 20.0, 0.0));

    TopoDS_Shape aTopoSphere = BRepPrimAPI_MakeSphere(anAxis, 3.0).Shape();
    Handle(AIS_Shape) anAisSphere = new AIS_Shape(aTopoSphere);

    anAisSphere->SetColor(Quantity_NOC_BLUE1);

    display->getContext()->Display(anAisSphere);
}*/