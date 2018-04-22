#from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtOpenGL import *

from OCC.V3d import V3d_Viewer
from OCC.Aspect import Aspect_DisplayConnection

import sys

class DisplayWidget(QGLWidget):
	def __init__(self, parent):
		QGLWidget.__init__(self, parent)

		self.m_viewer = None
		self.m_view = None
		self.m_context = None


	def paintEvent(self, e):
		print("paintEvent")

		if(self.m_context == None):
			self.init()
#    if (m_context.IsNull()) {
#        init();
#        for (auto& wrap : display_on_init_list) {
#            Handle(AIS_Shape) anAisBox1 = new AIS_Shape(wrap->native);
#            Handle(AIS_Shape) anAisBox2 = new AIS_Shape(wrap->native);
#
#            Quantity_Color shpcolor (0.6, 0.6, 0.8,  Quantity_TOC_RGB);  
#            anAisBox1->SetColor(shpcolor);
#            getContext()->Display(anAisBox1, false);
#            
#            anAisBox2->SetColor(Quantity_NOC_BLACK);
#            anAisBox2->SetDisplayMode(AIS_WireFrame);  
#            getContext()->Display(anAisBox2, false);
#            m_view->FitAll (0.5, false);
#        }
#    }
#
#    m_view->Redraw();
#}

	def init(self):
		aDisplayConnection = Aspect_DisplayConnection();

#   // Get graphic driver if it exists, otherwise initialise it
#   if (GetGraphicDriver().IsNull()) {
#       GetGraphicDriver() = new OpenGl_GraphicDriver(aDisplayConnection);
#   }

#   // Get window handle. This returns something suitable for all platforms.
#   WId window_handle = (WId) winId();

#   // Create appropriate window for platform
#   #ifdef WNT
#       Handle(WNT_Window) wind = new WNT_Window((Aspect_Handle) window_handle);
#   #elif defined(__APPLE__) && !defined(MACOSX_USE_GLX)
#       Handle(Cocoa_Window) wind = new Cocoa_Window((NSView *) window_handle);
#   #else
#       Handle(Xw_Window) wind = new Xw_Window(aDisplayConnection, (Window) window_handle);
#   #endif

#   // Create V3dViewer and V3d_View
#   m_viewer = new V3d_Viewer(GetGraphicDriver(), (Standard_ExtString)"viewer");

#   m_view = m_viewer->CreateView();

#   m_view->SetWindow(wind);
#   if (!wind->IsMapped()) wind->Map();

#   // Create AISInteractiveContext
#   m_context = new AIS_InteractiveContext(m_viewer);

#   // Set up lights etc
#   //m_viewer->SetDefaultLights();
#   m_viewer->SetLightOn (new V3d_DirectionalLight (m_viewer, V3d_Zneg , Quantity_NOC_WHITE, true));
#   //m_viewer->SetLightOn(new V3d_AmbientLight (m_viewer, Quantity_NOC_BLUE1));

#   //m_view->SetBackgroundColor(Quantity_NOC_FOREST);
#   m_view->MustBeResized();
#   m_view->TriedronDisplay(Aspect_TOTP_LEFT_LOWER, Quantity_NOC_GOLD, 0.08, V3d_ZBUFFER);

#   //m_context->SetDisplayMode(AIS_Shaded, false);
#   m_context->SetDisplayMode(AIS_Shaded, false);
#   //m_context->SetHilightColor(Quantity_NOC_AZURE);

#   m_view->SetBgGradientColors(
#       Quantity_Color(0.5,0.5,0.5,Quantity_TOC_RGB), 
#       Quantity_Color(0.3,0.3,0.3,Quantity_TOC_RGB), 
#       Aspect_GFM_VER, 
#       Standard_False
#   );


class ZenWidget(QMainWindow):
	def __init__(self):
		QMainWindow.__init__(self)

		self.createActions()
		self.createMenus()
		self.createStatusBar()

		self.display = DisplayWidget(self)
		self.setCentralWidget(self.display);
		self.resize(640, 480);

	def createActions(self):
		self.exitAct = QAction(self.tr("E&xit"), self)
		self.exitAct.setShortcut(self.tr("Ctrl+Q"))
		self.exitAct.setStatusTip(self.tr("Exit the application"))
		self.exitAct.triggered.connect(sys.exit)

		self.aboutAct = QAction(self.tr("&About"), self)
		self.aboutAct.setStatusTip(self.tr("Show the application's About box"))
		self.aboutAct.triggered.connect(self.aboutHandler)
		
	def createMenus(self):
		self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
		self.fileMenu.addAction(self.exitAct)

		self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
		self.helpMenu.addAction(self.aboutAct)
		
	def createStatusBar(self):
		pass

	def aboutHandler(self):
		QMessageBox.about(self, "About ZenWidget",
			"<h2>ZenWidget</h2>"
			"<p>Author: mirmik(mirmikns@yandex.ru) 2018"
			"<p>ZenCad shower."
			"<p>Based on occQt demo applicaton."
		)
		
		

	#QAction* mStlExport;
   #QAction* mExitAction;

   #//! show the about info action.
   #QAction* mAboutAction;

   #//! the menus of the application.
   #QMenu* mFileMenu;
   #//QMenu* mViewMenu;
   #//QMenu* mPrimitiveMenu;
   #//QMenu* mModelingMenu;
   #QMenu* mHelpMenu;

   #//! the toolbars of the application.
   #//QToolBar* mViewToolBar;
   #//QToolBar* mNavigateToolBar;
   #//QToolBar* mPrimitiveToolBar;
   #//QToolBar* mModelingToolBar;
   #//QToolBar* mHelpToolBar;

#public:
#    DisplayWidget* display;
#
#private:
#    void createActions();
#    void createMenus();
#    void createToolbars();
#
#private slots:
#    void about(void);
#    void export_stl();
#
#public:
#	ZenWidget(QWidget* parent = nullptr);

def show():
	QApplication.setDesktopSettingsAware(False)
	app = QApplication(sys.argv)
	
	w = ZenWidget()
	w.show()

	app.exec()