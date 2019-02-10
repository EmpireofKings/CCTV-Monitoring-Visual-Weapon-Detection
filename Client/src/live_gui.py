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
import base64 as b64
from collections import deque

class LiveAnalysis(QWidget):
	def __init__(self, app):
		QWidget.__init__(self)
		layout = QHBoxLayout()

		#get building data
		buildingFile = open("../data/config.json", 'r')
		buildingData = json.load(buildingFile)

		#System Overview (left side)
		buildingView = BuildingViewer(app, buildingData)
		layout.addWidget(buildingView)

		#Camera monitoring (right side)
		self.cameraView = CameraViewer(app, buildingData, buildingView)
		layout.addWidget(self.cameraView)

		self.setLayout(layout)

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
		#self.setFrameStyle(QFrame.Box)
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
