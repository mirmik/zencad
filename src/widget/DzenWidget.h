#ifndef DZENCAD_DZENWIDGET_H
#define DZENCAD_DZENWIDGET_H

#include <QtWidgets/QMenuBar>
#include <QtWidgets/QMainWindow>
#include <DisplayWidget.h>

class DzenWidget : public QMainWindow {
	Q_OBJECT

    //! the exit action.
    QAction* mExitAction;

    //! test algorithm
    QAction* mMakeBoxAction;
    QAction* mMakeSphereAction;
    QAction* mMakeConeAction;

    //! show the about info action.
    QAction* mAboutAction;

    //! the menus of the application.
    QMenu* mFileMenu;
    //QMenu* mViewMenu;
    QMenu* mPrimitiveMenu;
    //QMenu* mModelingMenu;
    QMenu* mHelpMenu;

    //! the toolbars of the application.
    //QToolBar* mViewToolBar;
    //QToolBar* mNavigateToolBar;
    //QToolBar* mPrimitiveToolBar;
    //QToolBar* mModelingToolBar;
    //QToolBar* mHelpToolBar;

public:
    DisplayWidget* display;

private:
    void createActions();
    void createMenus();
    void createToolbars();

private slots:
    void about(void);

    void makeBox(void);
    void makeSphere(void);
    void makeCone(void);

public:
	DzenWidget(QWidget* parent = nullptr);


};

#endif