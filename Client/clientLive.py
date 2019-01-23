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
import clientHelper as ch


class LiveAnalysis():
	def __init__(self, helper):
		self.layout = QHBoxLayout()
		self.helper = helper

		#System Overview (left side)
		buildingView = BuildingViewer(helper)
		self.layout.addWidget(buildingView)

		cameraIDs = buildingView.cameras
		#Camera monitoring (right side)
		cameraView = CameraViewer(cameraIDs)
		self.layout.addWidget(cameraView)

	def getLayout(self):
		return self.layout

#### LEFT SIDE ####
class BuildingViewer(QFrame):
	def __init__(self, helper):
		QFrame.__init__(self)
		availableSpace = helper.getScreenParams()
		print(availableSpace)
		self.setMinimumSize(QSize(availableSpace[0]*.33,int(availableSpace[1]*.75)))

		#self.setFrameStyle(QFrame.Box)
		buildingFile = open("./data/building.json", 'r')
		self.buildingData = json.load(buildingFile)
		levels = self.buildingData["levelIDs"]
		self.cameras = self.buildingData["cameraIDs"]

		layout = QVBoxLayout()
		self.drawSpace = BuildingPainter(helper, self.buildingData)
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
		current = int(self.dropdown.currentText()[len("Label "):])

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
		index = int(self.dropdown.currentText()[len("Label "):])
		self.drawSpace.currentLevel = index
		self.drawSpace.repaint()

class BuildingPainter(QFrame):
	def __init__(self, helper, buildingData):
		QFrame.__init__(self)
		self.buildingData = buildingData
		self.currentLevel = 0
		availableSpace = helper.getScreenParams()
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
	def __init__(self, cameraIDs):
		QFrame.__init__(self)
		self.setFrameStyle(QFrame.Box)
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

		maxCols = 3
		rows = int(math.ceil((len(cameraIDs)/maxCols)))

		count = 0
		for row in range(rows):
			for col in range(maxCols):
				if count < len(cameraIDs):
					display = CameraDisplay(QSize(256,144), cameraIDs[count])
					layout.addLayout(display, row, col)
					t = Thread(target=loadThread, daemon=True, args=[display, (256,144), cameraIDs[count]])
					t.start()
					count += 1
				else:
					break

		self.setLayout(layout)

class CameraDisplay(QHBoxLayout):
	newFrameSignal = Signal(ch.FramePack)

	def __init__(self, minSize, cameraID):
		QHBoxLayout.__init__(self)
		surface = CameraSurface(minSize, cameraID)
		self.newFrameSignal.connect(surface.updateDisplay)
		self.cameraID = cameraID
		self.addWidget(surface)

	def newFrameReady(self, framePack):
		#if global main id = self if, also emit to update main display with same frame pack
		self.newFrameSignal.emit(framePack)

class CameraSurface(QLabel):
	def __init__(self, minSize, cameraID):
		QLabel.__init__(self)
		self.setMinimumSize(minSize)
		self.setMaximumSize(minSize)
		self.cameraID = cameraID

	def updateDisplay(self, framePack):
		self.setPixmap(framePack.getFrameAsPixmap())
	# def mousePressEvent(self, event):
	# 	print(self.cameraID)

### THREAD FUNCTIONS ###
def loadThread(display, size, id):
	feed = cv2.VideoCapture(id)
	vidFPS = feed.get(cv2.CAP_PROP_FPS)
	#print(vidFPS, id)

	cur = time.time()
	while feed.isOpened():
		check, frame = feed.read()

		if check == True:
			frame = cv2.resize(frame, size)
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

			#FPS Control
			while((time.time() - cur) < 1/vidFPS) :time.sleep(0.01)

			fp = ch.FramePack(frame, id)
			display.newFrameReady(fp)
			cur = time.time()
		else:
			feed.set(cv2.CAP_PROP_POS_FRAMES, 0)
			#print("reset")
