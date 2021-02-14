from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import zencad
import random
import time
import os

class ScreenSaverWidget(QWidget):
	def __init__(self, text=None, color=QColor(137,40,151)):
		if text is None:
			text = "Loading... please wait."

		self.text = text
		self.subtext = ["", "", ""]
		self.color = color
		self.last_install_time = time.time()
		self.mode="techpriest"
		super().__init__()

	def set_background(self, bg):
		self.background_pixmap = bg
		#self.background_pixmap_dark = bg.copy(0,0,bg.width(),bg.height())


	def set_error_state(self):
		self.mode = "error"
		self.set_text("Error in loaded script")
		self.subtext=["","",""]

	def drop_background(self):
		self.background_pixmap = None

	def set_loading_state(self):
		self.mode = "load"
		if sys.platform == "darwin":
			self.set_text("Loading ... (embeding not supported for osx)")
		else:
			self.set_text("Loading ...")
		self.last_install_time = time.time()

	def set_text(self, text):
		self.text = text
		self.update()

	def set_subtext(self, lvl, text):
		self.subtext[lvl] = text
		self.update()

	def black_box_paint(self, ev):
		painter = QPainter(self)
		painter.setPen(Qt.white)
		
		if self.background_pixmap == None:
			painter.setBrush(Qt.black)
			painter.drawRect(0,0,self.width(),self.height())
		else:
			if time.time() - self.last_install_time < 0.7 and self.mode!="error":
				painter.drawPixmap(0,0,self.width(),self.height(), self.background_pixmap)
			else:
				painter.drawPixmap(0,0,self.width(),self.height(), self.background_pixmap)
				painter.fillRect(QRect(0, 0, self.width(), self.height()), QBrush(QColor(0, 0, 0, 200)))

		font = QFont()
		font.setPointSize(16)
		painter.setFont(font)
	
		message = self.text

		if time.time() - self.last_install_time > 0.7 or self.mode=="error":
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(message)/2,
					self.height()/2 - 1 * QFontMetrics(font).height()), 
					message)
	
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(self.subtext[0])/2,
					self.height()/2 + 0 *QFontMetrics(font).height()), 
					self.subtext[0])
	
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(self.subtext[1])/2,
					self.height()/2 + 1*QFontMetrics(font).height()), 
					self.subtext[1])
	
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(self.subtext[2])/2,
					self.height()/2 + 2*QFontMetrics(font).height()), 
					self.subtext[2])

		QTimer.singleShot(750, self.repaint)
		
	def basePaintEvent(self, ev):
		pathes = ["techpriest.jpg"]

		painter = QPainter(self)
		painter.setPen(self.color)
		painter.setBrush(QColor(218,216,203))
		painter.drawRect(0,0,self.width(),self.height())
		bird = QImage(os.path.join(zencad.moduledir, random.choice(pathes)))
		
		bw = bird.width()
		bh = bird.height()
		w = self.width()
		h = self.height()
		kw = bw / w
		kh = bh / h

		if kh >= kw:
			bw = bw / kh
			cw = self.width() / 2
			painter.drawImage(QRect(cw-bw/2,0,bw,self.height()), bird)
		else:
			bh = bh / kw
			ch = self.height() / 2
			painter.drawImage(QRect(0,ch-bh/2,self.width(),bh), bird)


		font = QFont()
		font.setPointSize(12)
		painter.setFont(font)

		bind_widget_flag = zencad.settings.get(["gui", "bind_widget"])
		if not bind_widget_flag == "false":
			message = self.text
		
			painter.drawText(
				QPoint(
					self.width()/2 - QFontMetrics(font).width(message)/2,
					QFontMetrics(font).height()), 
				message)
		painter.end()

	def paintEvent(self, ev):
		if self.mode == "error":
			self.black_box_paint(ev)
		elif self.mode == "load":
			self.black_box_paint(ev)
		else: 
			self.basePaintEvent(ev)