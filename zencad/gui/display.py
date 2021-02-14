#!/usr/bin/env python3

import sys
import os

from OCC.Core.AIS import AIS_Axis, AIS_Shaded
from OCC.Core.Aspect import Aspect_GFM_VER
from OCC.Core.Quantity import Quantity_TOC_RGB, Quantity_Color
from OCC.Core.Geom import Geom_Line
from OCC.Core.gp import gp_Lin, gp_Pnt, gp_Dir, gp_XYZ

from OCC.Display import OCCViewer
from OCC.Display.backend import get_qt_modules

import OCC.Core.BRepPrimAPI

QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()

class qtBaseViewer(QtOpenGL.QGLWidget):
	''' The base Qt Widget for an OCC viewer
	'''
	def __init__(self, parent=None):
		super(qtBaseViewer, self).__init__(parent)
		self._display = OCCViewer.Viewer3d()
		self._inited = False

		# enable Mouse Tracking
		self.setMouseTracking(True)

		# Strong focus
		self.setFocusPolicy(QtCore.Qt.WheelFocus)

		self.setAttribute(QtCore.Qt.WA_NativeWindow)
		self.setAttribute(QtCore.Qt.WA_PaintOnScreen)
		self.setAttribute(QtCore.Qt.WA_NoSystemBackground)

		self.setAutoFillBackground(False)
		
		color1= Quantity_Color(.55,.55,.55, Quantity_TOC_RGB)
		color2= Quantity_Color(.22,.22,.22, Quantity_TOC_RGB)
		self._display.View.SetBgGradientColors(color1, color2, Aspect_GFM_VER, True)

	def resizeEvent(self, event):
		super(qtBaseViewer, self).resizeEvent(event)
		self._display.View.MustBeResized()

	def paintEngine(self):
		return None


class DisplayWidget(qtBaseViewer):

	# emit signal when selection is changed
	# is a list of TopoDS_*
	#if HAVE_PYQT_SIGNAL:
	#    sig_topods_selected = QtCore.pyqtSignal(list)

	def __init__(self, 
		axis_triedron=True,
		bind_mode=False,
		communicator = None):
		
		qtBaseViewer.__init__(self)
		self.setObjectName("qt_viewer_3d")

		self._bind_mode = bind_mode
		self._communicator = communicator

		self._drawbox = False
		self._zoom_area = False
		self._select_area = False
		self._inited = False
		self._leftisdown = False
		self._middleisdown = False
		self._rightisdown = False
		self._selection = None
		self._drawtext = True
		self._qApp = QtWidgets.QApplication.instance()

		self.make_axis_triedron()
		if axis_triedron:
			self.enable_axis_triedron(True)

	def make_axis_triedron(self):
		self.x_axis = AIS_Axis(Geom_Line(gp_Lin(gp_Pnt(0,0,0),gp_Dir(gp_XYZ(1,0,0)))))
		self.y_axis = AIS_Axis(Geom_Line(gp_Lin(gp_Pnt(0,0,0),gp_Dir(gp_XYZ(0,1,0)))))
		self.z_axis = AIS_Axis(Geom_Line(gp_Lin(gp_Pnt(0,0,0),gp_Dir(gp_XYZ(0,0,1)))))
		self.x_axis.SetColor(Quantity_Color(1,0,0,Quantity_TOC_RGB))
		self.y_axis.SetColor(Quantity_Color(0,1,0,Quantity_TOC_RGB))
		self.z_axis.SetColor(Quantity_Color(0,0,1,Quantity_TOC_RGB))

	def attach_scene(self, scene):
		scene.display = self

		for iobj in scene.interactives:
			iobj.bind_context(self._display.GetContext())
			self._display.GetContext().Display(iobj.ais_object, True)

	def autoscale(self, koeff=0.07):
		self._display.GetView().FitAll(koeff)
		self._display.GetView().Redraw()

	def enable_axis_triedron(self, en):
		if en:
			self._display.GetContext().Display(self.x_axis, True)
			self._display.GetContext().Display(self.y_axis, True)
			self._display.GetContext().Display(self.z_axis, True)
		else:
			self._display.GetContext().Erase(self.x_axis, True)
			self._display.GetContext().Erase(self.y_axis, True)
			self._display.GetContext().Erase(self.z_axis, True)

	@property
	def qApp(self):
		# reference to QApplication instance
		return self._qApp

	@qApp.setter
	def qApp(self, value):
		self._qApp = value

	def InitDriver(self):
		self._display.Create(window_handle=int(self.winId()), parent=self)
		# background gradient
#		self._display.SetModeShaded()
		
		self._display.GetViewer().SetDefaultLights();
		self._display.GetViewer().SetLightOn();

		self._display.GetContext().SetDisplayMode(AIS_Shaded, False);
		self._display.GetContext().DefaultDrawer().SetFaceBoundaryDraw(True);

		self._inited = True
		
		self.autoscale()

	def keyPressEvent(self, event):
		code = event.key()
		if code in self._key_map:
			self._key_map[code]()
		elif code in range(256):
			log.info('key: "%s"(code %i) not mapped to any function' % (chr(code), code))
		else:
			log.info('key: code %i not mapped to any function' % code)

	def focusInEvent(self, event):
		if self._inited:
			self._display.Repaint()

	def focusOutEvent(self, event):
		if self._inited:
			self._display.Repaint()

	def paintEvent(self, event):
		if not self._inited:
			self.InitDriver()

			if self._bind_mode:
				self._communicator.send({
					"cmd":"bindwin", 
					"id":int(self.winId()), 
					"pid":os.getpid(), 
					#"session_id":self.session_id
				})

				QtGui.QWindow.fromWinId(self.winId()).setFlags(
					QtGui.QWindow.fromWinId(self.winId()).flags() | 
					QtCore.Qt.SubWindow) 

		self._display.Context.UpdateCurrentViewer()

		if self._drawbox:
			painter = QtGui.QPainter(self)
			painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))
			rect = QtCore.QRect(*self._drawbox)
			painter.drawRect(rect)

	def wheelEvent(self, event):
		delta = event.angleDelta().y()
		if delta > 0:
			zoom_factor = 2.
		else:
			zoom_factor = 0.5
		self._display.ZoomFactor(zoom_factor)

	def mousePressEvent(self, event):
		self.setFocus()
		ev = event.pos()
		self.dragStartPosX = ev.x()
		self.dragStartPosY = ev.y()
		self._display.StartRotation(self.dragStartPosX, self.dragStartPosY)

	def mouseReleaseEvent(self, event):
		pt = event.pos()
		modifiers = event.modifiers()

		if event.button() == QtCore.Qt.LeftButton:
			if self._select_area:
				[Xmin, Ymin, dx, dy] = self._drawbox
				self._display.SelectArea(Xmin, Ymin, Xmin + dx, Ymin + dy)
				self._select_area = False
			else:
				# multiple select if shift is pressed
				if modifiers == QtCore.Qt.ShiftModifier:
					self._display.ShiftSelect(pt.x(), pt.y())
				else:
					# single select otherwise
					self._display.Select(pt.x(), pt.y())

					#if (self._display.selected_shapes is not None) and HAVE_PYQT_SIGNAL:
					#    self.sig_topods_selected.emit(self._display.selected_shapes)


		elif event.button() == QtCore.Qt.RightButton:
			if self._zoom_area:
				[Xmin, Ymin, dx, dy] = self._drawbox
				self._display.ZoomArea(Xmin, Ymin, Xmin + dx, Ymin + dy)
				self._zoom_area = False

		self.cursor = "arrow"

	def DrawBox(self, event):
		tolerance = 2
		pt = event.pos()
		dx = pt.x() - self.dragStartPosX
		dy = pt.y() - self.dragStartPosY
		if abs(dx) <= tolerance and abs(dy) <= tolerance:
			return
		self._drawbox = [self.dragStartPosX, self.dragStartPosY, dx, dy]


	def mouseMoveEvent(self, evt):
		pt = evt.pos()
		buttons = int(evt.buttons())
		modifiers = evt.modifiers()
		# ROTATE
		if (buttons == QtCore.Qt.LeftButton and
				not modifiers == QtCore.Qt.ShiftModifier):
			self.cursor = "rotate"
			self._display.Rotation(pt.x(), pt.y())
			self._drawbox = False
		# DYNAMIC ZOOM
		elif (buttons == QtCore.Qt.RightButton and
			  not modifiers == QtCore.Qt.ShiftModifier):
			self.cursor = "zoom"
			self._display.Repaint()
			self._display.DynamicZoom(abs(self.dragStartPosX),
									  abs(self.dragStartPosY), abs(pt.x()),
									  abs(pt.y()))
			self.dragStartPosX = pt.x()
			self.dragStartPosY = pt.y()
			self._drawbox = False
		# PAN
		elif buttons == QtCore.Qt.MidButton:
			dx = pt.x() - self.dragStartPosX
			dy = pt.y() - self.dragStartPosY
			self.dragStartPosX = pt.x()
			self.dragStartPosY = pt.y()
			self.cursor = "pan"
			self._display.Pan(dx, -dy)
			self._drawbox = False
		# DRAW BOX
		# ZOOM WINDOW
		elif (buttons == QtCore.Qt.RightButton and
			  modifiers == QtCore.Qt.ShiftModifier):
			self._zoom_area = True
			self.cursor = "zoom-area"
			self.DrawBox(evt)
			self.update()
		# SELECT AREA
		elif (buttons == QtCore.Qt.LeftButton and
			  modifiers == QtCore.Qt.ShiftModifier):
			self._select_area = True
			self.DrawBox(evt)
			self.update()
		else:
			self._drawbox = False
			self._display.MoveTo(pt.x(), pt.y())
			self.cursor = "arrow"

#qapp = QtWidgets.QApplication(sys.argv[1:]) 
#disp = qtViewer3d()

#my_box = OCC.Core.BRepPrimAPI.BRepPrimAPI_MakeBox(10., 20., 30.).Shape()
#disp._display.DisplayShape(my_box, update=True)

#disp.show()
#qapp.exec()