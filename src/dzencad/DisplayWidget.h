#ifndef DZENCAD_DISPLAYWIDGET_H
#define DZENCAD_DISPLAYWIDGET_H

#include <QtOpenGL/QGLWidget>
#include <AIS_InteractiveContext.hxx>

#include <gxx/math/quaternion.h>

#include <memory>
#include <dzencad/base.h>
#include <dzencad/topo.h>

class DisplayWidget : public QGLWidget {
	Q_OBJECT

public:
    Handle(V3d_Viewer) m_viewer;
    Handle(V3d_View) m_view;
    Handle(AIS_InteractiveContext) m_context;

private:
	QPoint temporary1;
    malgo::quaternion<double> quat_orient;

    double phi = - cos(M_PI / 4);
    double psi = 0.61548;//cos(M_PI / 4);

public:
    void init();
    std::vector<TopoDS_Shape> display_on_init_list;

protected:
    // Paint events.
    virtual void showEvent(QShowEvent* e) override;
    virtual void paintEvent(QPaintEvent* e) override;
    virtual void resizeEvent(QResizeEvent* e) override;

    // Mouse events.
    virtual void mousePressEvent(QMouseEvent* e) override;
    virtual void mouseReleaseEvent(QMouseEvent* e) override;
    virtual void mouseMoveEvent(QMouseEvent * e) override;
    virtual void wheelEvent(QWheelEvent * e) override;

    // Button events.
    virtual void onLButtonDown(const int theFlags, const QPoint thePoint);
    virtual void onMButtonDown(const int theFlags, const QPoint thePoint);
    virtual void onRButtonDown(const int theFlags, const QPoint thePoint);
    virtual void onMouseWheel(const int theFlags, const int theDelta, const QPoint thePoint);
    virtual void onLButtonUp(const int theFlags, const QPoint thePoint);
    virtual void onMButtonUp(const int theFlags, const QPoint thePoint);
    virtual void onRButtonUp(const int theFlags, const QPoint thePoint);
    virtual void onMouseMove(const int theFlags, const QPoint thePoint);

    // Popup menu.
    //virtual void addItemInPopup(QMenu* theMenu);

public:
	DisplayWidget(QWidget* parent = nullptr) : QGLWidget(parent) {
    	setBackgroundRole( QPalette::NoRole );
	}

    ~DisplayWidget() {
        gxx::println("~DisplayWidget");
        //delete m_view;
        //delete m_viewer;
        //delete m_context;
    }

public:
    const Handle_AIS_InteractiveContext& getContext() const;
};

#endif