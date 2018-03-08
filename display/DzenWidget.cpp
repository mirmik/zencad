#include <DzenWidget.h>
#include <QtWidgets/QMessageBox>

#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <AIS_Shape.hxx>

void DzenWidget::createActions() {
    mExitAction = new QAction(tr("Exit"), this);
    mExitAction->setShortcut(tr("Ctrl+Q"));
    //mExitAction->setIcon(QIcon(":/Resources/close.png"));
    mExitAction->setStatusTip(tr("Exit the application"));
    connect(mExitAction, SIGNAL(triggered()), this, SLOT(close()));

    mMakeBoxAction = new QAction(tr("Box"), this);
    //mMakeBoxAction->setIcon(QIcon(":/Resources/box.png"));
    mMakeBoxAction->setStatusTip(tr("Make a box"));
    connect(mMakeBoxAction, SIGNAL(triggered()), this, SLOT(makeBox()));

    mMakeConeAction = new QAction(tr("Cone"), this);
    //mMakeConeAction->setIcon(QIcon(":/Resources/cone.png"));
    mMakeConeAction->setStatusTip(tr("Make a cone"));
    connect(mMakeConeAction, SIGNAL(triggered()), this, SLOT(makeCone()));

    mMakeSphereAction = new QAction(tr("Sphere"), this);
    mMakeSphereAction->setStatusTip(tr("Make a sphere"));
    //mMakeSphereAction->setIcon(QIcon(":/Resources/sphere.png"));
    connect(mMakeSphereAction, SIGNAL(triggered()), this, SLOT(makeSphere()));

    mAboutAction = new QAction(tr("About"), this);
    mAboutAction->setStatusTip(tr("About the application"));
    //mAboutAction->setIcon(QIcon(":/Resources/lamp.png"));
    connect(mAboutAction, SIGNAL(triggered()), this, SLOT(about()));
}

void DzenWidget::createMenus() {
    mFileMenu = menuBar()->addMenu(tr("&File"));
    mFileMenu->addAction(mExitAction);

    /*mViewMenu = menuBar()->addMenu(tr("&View"));
    mViewMenu->addAction(mViewZoomAction);
    mViewMenu->addAction(mViewPanAction);
    mViewMenu->addAction(mViewRotateAction);
    mViewMenu->addSeparator();
    mViewMenu->addAction(mViewResetAction);
    mViewMenu->addAction(mViewFitallAction);
    */
    mPrimitiveMenu = menuBar()->addMenu(tr("&Primitive"));
    mPrimitiveMenu->addAction(mMakeBoxAction);
    mPrimitiveMenu->addAction(mMakeConeAction);
    mPrimitiveMenu->addAction(mMakeSphereAction);
    //mPrimitiveMenu->addAction(mMakeCylinderAction);
    //mPrimitiveMenu->addAction(mMakeTorusAction);

    /*mModelingMenu = menuBar()->addMenu(tr("&Modeling"));
    mModelingMenu->addAction(mFilletAction);
    mModelingMenu->addAction(mChamferAction);
    mModelingMenu->addAction(mExtrudeAction);
    mModelingMenu->addAction(mRevolveAction);
    mModelingMenu->addAction(mLoftAction);
    mModelingMenu->addSeparator();
    mModelingMenu->addAction(mCutAction);
    mModelingMenu->addAction(mFuseAction);
    mModelingMenu->addAction(mCommonAction);
    mModelingMenu->addSeparator();
    mModelingMenu->addAction(myHelixAction);*/

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


void DzenWidget::makeBox() {
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
}