#TODO

import numpy as np
import cv2
import sys
import json
import math
from pprint import pprint
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from threading import Thread
import time
import os
import json

class Config(QWidget):
	def __init__(self, app, configHandler):
		QWidget.__init__(self)

		layout = QHBoxLayout()

		self.levelMenu = LevelMenu(configHandler)

		drawSpace = BuildingPainter(configHandler)
		controls = Controls(drawSpace, configHandler)

		middleSection = QVBoxLayout()
		middleSection.addWidget(drawSpace)
		middleSection.addWidget(controls)

		self.cameraMenu = CameraMenu(configHandler)

		layout.addWidget(self.levelMenu)
		layout.addLayout(middleSection)
		layout.addWidget(self.cameraMenu)

		self.setLayout(layout)

class LevelMenu(QScrollArea):
	def __init__(self, configHandler):
		QScrollArea.__init__(self)
		levels = configHandler.getConfigData()

		self.layout = QVBoxLayout()

		for level in levels:
			disp = LevelDisplay(level)
			self.layout.addWidget(disp)



		self.mainWidget = QWidget()
		self.mainWidget.setLayout(self.layout)
		self.setWidget(self.mainWidget)


class LevelDisplay(QLabel):
	def __init__(self, level):
		QLabel.__init__(self)
		self.setMaximumSize(QSize(256, 144))
		self.level = level

		pmap = QPixmap(level.drawPath).scaled(QSize(self.width(), self.height()), Qt.KeepAspectRatio)
		self.setPixmap(pmap)

	def mousePressEvent(self, event):
		print(str(self.level.id))

class CameraMenu(QScrollArea):
	def __init__(self, configHandler):
		QScrollArea.__init__(self)

		self.layout = QVBoxLayout()

		self.mainWidget = QWidget()
		self.mainWidget.setLayout(self.layout)
		self.setWidget(self.mainWidget)

class Controls(QWidget):
	def __init__(self, drawSpace, configHandler):
		QWidget.__init__(self)
		self.drawSpace = drawSpace

		colourButton = QPushButton("Colour")
		colourButton.clicked.connect(self.getColour)

		sizeButton = QPushButton("Size")
		saveButton = QPushButton("Save")
		resetButton = QPushButton("Reset")


		layout = QHBoxLayout()
		layout.addWidget(colourButton)
		layout.addWidget(sizeButton)
		layout.addWidget(saveButton)
		layout.addWidget(resetButton)

		self.setLayout(layout)

	def getColour(self):
		prompt = QColorDialog()
		result = prompt.getColor()

		if result.isValid():
			self.drawSpace.drawColour = result


class BuildingPainter(QFrame):
	def __init__(self, configHandler):
		QFrame.__init__(self)
		self.drawColour = QColor(0,0,0)
		self.setMinimumSize(QSize(700,700))
		self.setFrameStyle(QFrame.Box)
