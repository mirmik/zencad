#ifndef ZENCAD_VIEW
#define ZENCAD_VIEW

//debug
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>

#include <zencad/camera.h>
#include <zencad/scene.h>

struct ZenView {
	std::shared_ptr<ZenScene> scene;
	std::shared_ptr<ZenCamera> camera;

	//Handle(V3d_Viewer) m_viewer;
	Handle(V3d_View) m_view;

	void init() {
		m_view = scene->m_viewer->CreateView();
	}

	ZenView(std::shared_ptr<ZenScene> scene, std::shared_ptr<ZenCamera> camera) : scene(scene), camera(camera) {
		init();
	}

	void screen() {

		Standard_Integer  aDefWidth  = 800; 
		Standard_Integer  aDefHeight = 600; 
		//Handle  (Xw_WClass) aWClass =  new XW_WClass ("Virtual Class",DefWindowProc, 
		  //                            CS_VREDRAW | CS_HREDRAW, 0, 0,  
		    //                          ::LoadCursor (NULL, IDC_ARROW)); 

    	//WId window_handle = (WId) winId();
		Handle  (Xw_Window) aWindow =  new Xw_Window (scene->m_displayConnection, "virtual", 0, 0, 800, 800);
		// set up the window as  virtual
		aWindow->SetVirtual  (Standard_True); 
		m_view->SetWindow  (aWindow); 
		
		Handle (AIS_Shape) aBox = new AIS_Shape (BRepPrimAPI_MakeCylinder (40, 40).Shape()); 
		scene->m_context->Display  (aBox); 

		m_view->FitAll();
		m_view->Dump("3dscene.png"); 
	}
};

#endif