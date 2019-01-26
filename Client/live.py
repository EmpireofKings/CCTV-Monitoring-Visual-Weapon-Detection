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
import helper
import base64 as b64
from collections import deque

class LiveAnalysis():
	def __init__(self, app):
		self.layout = QHBoxLayout()

		#System Overview (left side)
		buildingView = BuildingViewer(app)
		self.layout.addWidget(buildingView)

		#Camera monitoring (right side)
		cameraView = CameraViewer(app, buildingView.cameras)
		self.layout.addWidget(cameraView)

	def getLayout(self):
		return self.layout

#### LEFT SIDE ####
class BuildingViewer(QFrame):
	def __init__(self, app):
		QFrame.__init__(self)

		#Space checks
		availableSpace = helper.getScreenParams(app)
		self.setMinimumSize(QSize(availableSpace[0]*.33,int(availableSpace[1]*.75)))

		#get building data
		buildingFile = open("./data/building.json", 'r')
		self.buildingData = json.load(buildingFile)

		levels = self.buildingData["levelIDs"]
		self.cameras = self.buildingData["cameraIDs"]

		#left side internal breakdown, painter and controls, vertically aligned
		layout = QVBoxLayout()
		self.drawSpace = BuildingPainter(app, self.buildingData)
		self.drawSpace.setFrameStyle(QFrame.Box)

		controlBox = QWidget()
		controlLayout = QHBoxLayout()
		upLevel = QPushButton("Up")
		downLevel = QPushButton("Down")

		upLevel.clicked.connect(self.updown)
		downLevel.clicked.connect(self.updown)

		self.dropdown = QComboBox()
		self.dropdown.currentIndexChanged.connect(self.changeLevel)

		for level in levels:
			self.dropdown.addItem("Level " + str(level))

		controlLayout.addWidget(upLevel)
		controlLayout.addWidget(downLevel)
		controlLayout.addWidget(self.dropdown)

		controlBox.setLayout(controlLayout)

		layout.addWidget(self.drawSpace)
		layout.addWidget(controlBox)

		self.setLayout(layout)

	def updown(self):
		current = int(self.dropdown.currentText()[len("Level "):])

		if self.sender().text() == "Up":
			current += 1
		elif self.sender().text() == "Down":
			current -= 1

		text = "Level " + str(current)
		index = self.dropdown.findText(text)

		if index != -1:
			self.dropdown.setCurrentIndex(index)
			self.changeLevel()

	def changeLevel(self):
		index = int(self.dropdown.currentText()[len("Level "):])
		self.drawSpace.currentLevel = index
		self.drawSpace.repaint()

class BuildingPainter(QFrame):
	def __init__(self, app, buildingData):
		QFrame.__init__(self)
		self.buildingData = buildingData
		self.currentLevel = 0 #start on ground level

		availableSpace = helper.getScreenParams(app)

		self.setMinimumSize(QSize(100,500))
		self.setMaximumSize(QSize(int(availableSpace[1]*.90),int(availableSpace[1]*.90)))

	def paintEvent(self, event):
		painter = QPainter(self)
		levels = self.buildingData["levelIDs"]
		curIndex = levels.index(int(self.currentLevel))
		self.levelData = self.buildingData["levelData"][curIndex]

		for line in self.levelData["LevelDrawCoordinates"]:
			p1 = QPoint(line[0][0], line[0][1])
			p2 = QPoint(line[1][0], line[1][1])

			painter.setPen(QColor(0,0,0))
			painter.drawLine(p1, p2)

		for cam in self.levelData["LevelCameras"]:
			point = QPointF(cam["cameraCoordinates"][0], cam["cameraCoordinates"][1])
			painter.setPen(QColor(0,255,0))
			painter.drawEllipse(point, 10, 10)#TODO SCALE SIZE


	def mousePressEvent(self, event):
		x1 = event.x()
		y1 = event.y()

		distDict = {}
		for cam in self.levelData["LevelCameras"]:
			id = cam["cameraID"]
			x2 = cam["cameraCoordinates"][0]
			y2 = cam["cameraCoordinates"][1]

			dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

			distDict[id] = dist

		closestID = min(distDict, key=distDict.get)


#### RIGHT SIDE ####

class CameraViewer(QFrame):
	def __init__(self, app, cameraIDs):
		QFrame.__init__(self)

		layout = QVBoxLayout()

		gridView = gridViewer(cameraIDs)

		scrollArea = QScrollArea()
		scrollArea.setWidget(gridView)
		scrollArea.setMinimumSize(QSize(800,500))

		layout.addWidget(scrollArea)

		self.setLayout(layout)

class gridViewer(QWidget):
	def __init__(self, cameraIDs):
		QWidget.__init__(self)

		layout = QGridLayout()

		maxCols = 3 #TODO, dynamically choose based on availale space
		rows = int(math.ceil((len(cameraIDs)/maxCols))) #figure out how many rows are needed based on amount of items and max cols

		count = 0 #item tracker
		for row in range(rows):
			for col in range(maxCols):
				if count < len(cameraIDs):#more slots than items to fill
					feedID = cameraIDs[count]

					display = CameraDisplay(QSize(256,144), feedID)
					layout.addLayout(display, row, col)

					nextFrame = deque(maxlen=1)
					loader = helper.FeedLoader(feedID)
					loader.setDaemon(True)
					loader.start()

					networker = helper.Networker(feedID, display)
					networker.setDaemon(True)
					networker.start()
					count += 1
				else:
					break

		self.setLayout(layout)

class CameraDisplay(QHBoxLayout):
	newFrameSignal = Signal(QPixmap)

	def __init__(self, minSize, cameraID):
		QHBoxLayout.__init__(self)
		surface = CameraSurface(minSize, cameraID)
		self.newFrameSignal.connect(surface.updateDisplay)
		self.cameraID = cameraID
		self.addWidget(surface)


class CameraSurface(QLabel):
	def __init__(self, minSize, cameraID):
		QLabel.__init__(self)
		self.setMinimumSize(minSize)
		self.setMaximumSize(minSize)
		self.cameraID = cameraID

	def updateDisplay(self, pmap):
		self.setPixmap(pmap)

	# def mousePressEvent(self, event):
	# 	print(self.cameraID)
