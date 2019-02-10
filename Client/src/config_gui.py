#TODO
from pprint import pprint
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from layout_gui import Layout, LayoutMode
from data_handler import *

class Config(QWidget):
	def __init__(self, app):
		QWidget.__init__(self)
		self.setMinimumSize(QSize(1280,800))

		layout = QHBoxLayout()

		dataLoader = DataLoader()
		data, _ = dataLoader.getConfigData()


		drawSpace = Layout(app, data, [LayoutMode.VIEW, LayoutMode.EDIT], self)

		self.levelMenu = LevelMenu(data, drawSpace)
		self.cameraMenu = CameraMenu(data, drawSpace)

		layout.addWidget(self.levelMenu)
		layout.addWidget(drawSpace)
		layout.addWidget(self.cameraMenu)

		self.setLayout(layout)

class LevelMenu(QScrollArea):
	def __init__(self, data, drawSpace):
		QScrollArea.__init__(self)
		self.drawSpace = drawSpace
		self.update(data)

	def update(self, data):
		self.layout = QVBoxLayout()
		self.setMaximumSize(QSize(300,1000))

		data.sort(key=lambda level: level.id)

		for level in data:
			disp = LevelDisplay(level, self.drawSpace)
			self.layout.addWidget(disp, Qt.AlignCenter)

		self.mainWidget = QFrame()
		self.mainWidget.setFrameStyle(QFrame.Box)
		self.mainWidget.setLayout(self.layout)
		self.setWidget(self.mainWidget)


class LevelDisplay(QLabel):
	def __init__(self, level, drawSpace):
		QLabel.__init__(self)
		self.setFrameStyle(QFrame.Box)
		self.drawSpace = drawSpace
		self.level = level
		pmap = getLabelledPixmap(256, 144, "Level " + str(self.level.id), self.level.drawPath)
		self.setPixmap(pmap)

	def mousePressEvent(self, event):
		self.drawSpace.controls.setLevel(self.level.id)

class CameraMenu(QScrollArea):
	def __init__(self, data, drawSpace):
		QScrollArea.__init__(self)

		self.layout = QVBoxLayout()
		self.setMaximumSize(QSize(300,1000))

		for level in data:
			for camera in level.cameras:
				disp = CameraDisplay(camera, drawSpace)
				self.layout.addWidget(disp, Qt.AlignCenter)

		self.mainWidget = QFrame()
		self.mainWidget.setFrameStyle(QFrame.Box)
		self.mainWidget.setLayout(self.layout)
		self.setWidget(self.mainWidget)

class CameraDisplay(QLabel):
	def __init__(self, camera, drawSpace):
		QLabel.__init__(self)
		self.setFrameStyle(QFrame.Box)
		self.drawSpace = drawSpace
		self.camera = camera

		pmap = camera.getPreview(256, 144)
		self.setPixmap(pmap)

	def mousePressEvent(self, event):
		self.drawSpace.controls.setMainFeedID(self.camera)
