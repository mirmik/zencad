#ifndef ZENCAD_SCENE
#define ZENCAD_SCENE

#include <OpenGl_GraphicDriver.hxx>
#undef Bool
#undef CursorShape
#undef None
#undef KeyPress
#undef KeyRelease
#undef FocusIn
#undef FocusOut
#undef FontChange
#undef Expose

#include <V3d_View.hxx>
#include <V3d_AmbientLight.hxx>
#include <V3d_DirectionalLight.hxx>

#include <Aspect_Handle.hxx>
#include <Aspect_DisplayConnection.hxx>

#ifdef WNT
  #include <WNT_Window.hxx>
#elif defined(__APPLE__) && !defined(MACOSX_USE_GLX)
  #include <Cocoa_Window.hxx>
#else
  #include <Xw_Window.hxx>
#endif
#include <AIS_InteractiveContext.hxx>
#include <AIS_Shape.hxx>

struct ZenScene {
	std::vector<std::shared_ptr<ZenShape>> shapes;
	void add(std::shared_ptr<ZenShape> shape) { shapes.push_back(shape); }
	void clear() { shapes.clear(); }

    Handle(V3d_Viewer) m_viewer;
    Handle(AIS_InteractiveContext) m_context;
    Handle(Aspect_DisplayConnection) m_displayConnection;

    static Handle(Graphic3d_GraphicDriver)& GetGraphicDriver() {
	    static Handle(Graphic3d_GraphicDriver) aGraphicDriver;
	    return aGraphicDriver;
	}
		
    void init() {
		if (GetGraphicDriver().IsNull()) {
			m_displayConnection = new Aspect_DisplayConnection();
			GetGraphicDriver() = new OpenGl_GraphicDriver(m_displayConnection);
		}

		m_viewer = new V3d_Viewer(GetGraphicDriver(), (Standard_ExtString)"viewer");
		m_context = new AIS_InteractiveContext (m_viewer); 
    }

    ZenScene() {
    	init();
    }
};

#endif