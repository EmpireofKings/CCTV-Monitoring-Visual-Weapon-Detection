import numpy as np
import cv2
import sys
import json
import math
from pprint import pprint
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class mainWindow(QMainWindow):
	def __init__(self):
		QMainWindow.__init__(self)
		items = ["Live Feed", "Existing Media"]
		decision = QInputDialog.getItem(self, "Analysis Type", "Please choose", items, editable=False)

		mainWidget = QWidget()

		if decision[0] == items[0]:
			layout = self.initLive()
			mainWidget.setLayout(layout)
		elif decision[0] == items[1]:
			mainWidget.setLayout(initExis())

		self.setCentralWidget(mainWidget)

	def initLive(self):
		layout = QHBoxLayout()

		#System Overview (left side)
		buildingView = BuildingViewer()
		layout.addWidget(buildingView)

		#Camera monitoring (right side)
		cameraLayout = QVBoxLayout()
		camPreviewLayout = QGridLayout()
		cameraPlaceholder = QLabel("Cameras placeholder")
		camPreviewLayout.addWidget(cameraPlaceholder,1 , 1)

		mainCamPlaceholder = QLabel("Main Cam placeholder")

		cameraLayout.addLayout(camPreviewLayout)
		cameraLayout.addWidget(mainCamPlaceholder)

		layout.addLayout(cameraLayout)

		return layout

	def initExis(self):
		layout = None
		#TODO: Setup existing media analysis layout
		return layout

class BuildingViewer(QWidget):
	def __init__(self):
		QWidget.__init__(self)
		self.setMinimumSize(QSize(500,600))

		buildingFile = open("./data/building.json", 'r')
		self.buildingData = json.load(buildingFile)
		levels = self.buildingData["levelIDs"]

		layout = QVBoxLayout()
		self.drawSpace = BuildingPainter(self.buildingData)

		self.controls = QHBoxLayout()
		label = QLabel("Building Levels: ")
		self.controls.addWidget(label)

		for level in levels:
			button = QPushButton(str(level))
			button.clicked.connect(self.changeLevel)
			self.controls.addWidget(button)

		layout.addWidget(self.drawSpace)
		layout.addLayout(self.controls)

		self.setLayout(layout)

	def changeLevel(self):
		self.drawSpace.currentLevel = self.sender().text()
		self.drawSpace.repaint()

class BuildingPainter(QWidget):
	def __init__(self, buildingData):
		QWidget.__init__(self)
		self.buildingData = buildingData
		self.currentLevel = 0

	def paintEvent(self, event):
		painter = QPainter(self)
		levels = self.buildingData["levelIDs"]
		print(levels)
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
		print(closestID)



if __name__ == '__main__':
	app = QApplication(sys.argv)
	mainWindow = mainWindow()
	mainWindow.show()
	sys.exit(app.exec_())
