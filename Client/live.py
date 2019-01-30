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
import threads
import base64 as b64
from collections import deque

class LiveAnalysis(QWidget):
	def __init__(self, app):
		QWidget.__init__(self)
		layout = QHBoxLayout()

		#get building data
		buildingFile = open("./data/building.json", 'r')
		buildingData = json.load(buildingFile)

		#System Overview (left side)
		buildingView = BuildingViewer(app, buildingData)
		layout.addWidget(buildingView)

		#Camera monitoring (right side)
		self.cameraView = CameraViewer(app, buildingData, buildingView)
		layout.addWidget(self.cameraView)

		self.setLayout(layout)

#### LEFT SIDE ####
class BuildingViewer(QFrame):
	def __init__(self, app, buildingData):
		QFrame.__init__(self)

		self.buildingData = buildingData

		self.drawSpace = BuildingPainter(app, self.buildingData)

		#CONTROLS
		upLevel = QPushButton("Up")
		downLevel = QPushButton("Down")
		upLevel.clicked.connect(self.buttonLevelChange)
		downLevel.clicked.connect(self.buttonLevelChange)

		self.dropdown = QComboBox()
		self.dropdown.currentIndexChanged.connect(self.dropdownLevelChange)

		levels = buildingData["LevelData"]
		for level in levels:
			self.dropdown.addItem("Level " + str(level["LevelID"]))

		controlLayout = QHBoxLayout()
		controlLayout.addWidget(upLevel)
		controlLayout.addWidget(downLevel)
		controlLayout.addWidget(self.dropdown)

		self.mainDisplay = FeedDisplayer(QSize(1280, 720), QSize(640, 360), None, self)

		layout = QVBoxLayout()
		layout.addWidget(self.drawSpace)
		layout.addLayout(controlLayout)
		layout.addWidget(self.mainDisplay)

		self.setLayout(layout)

	def buttonLevelChange(self):
		#get current level from button text
		current = int(self.dropdown.currentText()[len("Level "):])

		#determine which button was pressed
		if self.sender().text() == "Up":
			current += 1
		elif self.sender().text() == "Down":
			current -= 1

		#Find next level index in drop down
		text = "Level " + str(current)
		index = self.dropdown.findText(text)

		#if level exists in drop down change level
		if index != -1:
			self.dropdown.setCurrentIndex(index)
			#self.dropdownLevelChange()

	def dropdownLevelChange(self):
		index = int(self.dropdown.currentText()[len("Level "):])
		self.drawSpace.currentLevel = index
		self.drawSpace.repaint()

class BuildingPainter(QFrame):
	def __init__(self, app, buildingData):
		QFrame.__init__(self)
		self.buildingData = buildingData
		self.currentLevel = 0 #start on ground level

		self.levelData = self.buildingData["LevelData"]
		self.levels = []

		for level in self.levelData:
			self.levels.append(level["LevelID"])

		self.setFrameStyle(QFrame.Box)

		self.tooltip = QToolTip()
		self.setMinimumSize(QSize(500,500))

		self.setMouseTracking(True)

	def paintEvent(self, event):
		painter = QPainter(self)
		curIndex = self.levels.index(int(self.currentLevel))
		self.curData = self.levelData[curIndex]

		for line in self.curData["LevelDrawCoordinates"]:
			p1 = QPoint(line[0][0], line[0][1])
			p2 = QPoint(line[1][0], line[1][1])

			painter.setPen(QColor(0,0,0))
			painter.drawLine(p1, p2)

		for cam in self.curData["LevelCameras"]:
			id = cam["cameraID"]
			point = QPoint(cam["cameraCoordinates"][0], cam["cameraCoordinates"][1])
			orientation = cam["cameraOrientation"]


			if id != threads.mainFeedID:
				painter.setPen(QColor(0,0,255))
				painter.setBrush(QBrush(QColor(0,0,255), Qt.SolidPattern))
			else:
				painter.setBrush(Qt.NoBrush)
				painter.setPen(QColor(0,255,0))
				painter.drawEllipse(point, 10,10)

				painter.setBrush(QBrush(QColor(0,255,0), Qt.SolidPattern))

			painter.drawEllipse(point, 5, 5)#TODO SCALE SIZE


		#	painter.setPen(QPen(QColor(0,150,0), 1))

			#painter.drawArc(rect2, orientation-60, orientation+60)



	def mousePressEvent(self, event):
		id = self.getCloseCam(event.x(), event.y())

		if id is not None:
			threads.mainFeedID = id
			self.repaint()

	def mouseMoveEvent(self, event):
		pos = event.globalPos()
		id = self.getCloseCam(event.x(), event.y())

		if id is not None:
			self.tooltip.showText(pos, str(id))

	def getCloseCam(self, x1, y1):
		distDict = {}

		for cam in self.curData["LevelCameras"]:
			id = cam["cameraID"]
			x2 = cam["cameraCoordinates"][0]
			y2 = cam["cameraCoordinates"][1]

			dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

			distDict[id] = dist

		closestID = min(distDict, key=distDict.get)
		closestDist = distDict.get(closestID)

		if closestDist < 10:
			return closestID
		else:
			return None

#### RIGHT SIDE ####

class CameraViewer(QFrame):
	def __init__(self, app, buildingData, buildingView):
		QFrame.__init__(self)

		layout = QVBoxLayout()

		self.gridView = gridViewer(buildingData, buildingView)

		scrollArea = QScrollArea()
		scrollArea.setLayout(self.gridView)
		scrollArea.setMinimumSize(QSize(700,500))

		layout.addWidget(scrollArea)

		self.setLayout(layout)

class gridViewer(QGridLayout):
	def __init__(self, buildingData, buildingView):
		QGridLayout.__init__(self)
		self.setSpacing(10)
		self.setMargin(10)

		feeds = []

		levelData = buildingData["LevelData"]

		for level in levelData:
			lid = level["LevelID"]

			cameraData = level["LevelCameras"]

			for camera in cameraData:
				cid = camera["cameraID"]
				cameraLocation = camera["cameraLocation"]

				feeds.append({"level" : lid, "id" : cid, "location" : cameraLocation})

		# pprint(cameraIDs)
		# pprint(cameraLocations)
		#layout = QGridLayout()

		maxCols = 3 #TODO, dynamically choose based on availale space
		rows = int(math.ceil((len(feeds)/maxCols))) #figure out how many rows are needed based on amount of items and max cols

		count = 0 #item tracker
		for row in range(rows):
			for col in range(maxCols):
				if count < len(feeds):#more slots than items to fill
					feedData = feeds[count]

					## TODO TIDY THIS UP
					feedDisplayer = FeedDisplayer(QSize(384,216), QSize(128, 72), feedData, buildingView)
					self.addWidget(feedDisplayer, row, col)


					loader = threads.FeedLoader(feedData)
					loader.setDaemon(True)
					loader.start()

					networker = threads.Networker(feedData, feedDisplayer, buildingView.mainDisplay)
					networker.setDaemon(True)
					networker.start()

					count += 1
				else:
					break

class FeedDisplayer(QLabel):
	newFrameSignal = Signal(QPixmap)

	def __init__(self, maxSize, minSize, feedData, buildingView):
		QLabel.__init__(self)
		self.setFrameStyle(QFrame.Box)
		self.setMaximumSize(maxSize)
		self.setMinimumSize(minSize)
		self.buildingView = buildingView

		self.feedData = feedData
		self.newFrameSignal.connect(self.updateDisplay)

		camLayout = QVBoxLayout()
		camLayout.setMargin(0)
		camLayout.setSpacing(0)


		self.title = QLabel()
		self.title.setMaximumSize(150,20)
		camLayout.addWidget(self.title)

		self.surface = QLabel()

		camLayout.addWidget(self.surface)

		self.setLayout(camLayout)

	def updateDisplay(self, pmap):
		pmap = pmap.scaled(QSize(self.width(), self.height()), Qt.KeepAspectRatio)
		self.surface.setPixmap(pmap)
		self.title.setText("Level " + str(self.feedData["level"]) + " " + str(self.feedData["location"]))

	def mousePressEvent(self, event):
		if self.feedData is not None:
			threads.mainFeedID = self.feedData["id"]
			index = self.buildingView.dropdown.findText("Level " + str(self.feedData["level"]))

			#if level exists in drop down change level
			if index != -1:
				self.buildingView.dropdown.setCurrentIndex(index)
				self.buildingView.drawSpace.repaint()

		#	self.buildingView.dropdownLevelChange()
