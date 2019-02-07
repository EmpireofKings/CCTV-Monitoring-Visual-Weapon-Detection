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

class Config(QStackedWidget):
	def __init__(self, helper):
		QStackedWidget.__init__(self)

		settings = QWidget()
		settingsLayout = QVBoxLayout()
		buildingConfigButton = QPushButton("Configure Building")
		buildingConfigButton.clicked.connect(self.switchToConfig)
		settingsLayout.addWidget(buildingConfigButton)
		settings.setLayout(settingsLayout)

		self.buildingConfig = BuildingConfig()

		self.addWidget(settings)
		self.addWidget(self.buildingConfig)

	def switchToConfig(self):
		index = self.indexOf(self.buildingConfig)

		if index != -1:
			if os.path.isfile("../data/config.json"):
				prompt = QMessageBox()
				prompt.setText("A configuration file already exists, do you wish to open this file or reset it?")
				prompt.setIcon(QMessageBox.Question)
				prompt.setStandardButtons(QMessageBox.Open | QMessageBox.Reset | QMessageBox.Cancel)
				prompt.setDefaultButton(QMessageBox.Open)
				result = prompt.exec_()

				if result == QMessageBox.Open:
					self.setCurrentIndex(index)
					self.currentChanged(index)
				elif result == QMessageBox.Reset:
					self.setCurrentIndex(index)
					self.currentChanged(index)
					os.remove("../data/config.json")

		else:
			print("Error getting configuration index")


	def cycle(self):
		next = self.currentIndex() + 1
		total = self.count()


		if next >= total:
			next = 0

		self.setCurrentIndex(next)
		self.currentChanged(next)

	def currentChanged(self, index):
		#to officially begin the configuration
		print("currentChanged")
		if index == self.indexOf(self.buildingConfig):
			self.buildingConfig.begin()


class BuildingConfig(QWidget):
	def __init__(self):
		QWidget.__init__(self)
		layout = QHBoxLayout()

		levelScroll = QScrollArea()
		levelWidget = QWidget()
		levelLayout = QVBoxLayout()

		for i in range(0,100):
			levelLayout.addWidget(QLabel("level" + str(i)))

		levelWidget.setLayout(levelLayout)
		levelScroll.setWidget(levelWidget)

		middleDiv = QVBoxLayout()
		controls = QHBoxLayout()
		colourButton = QPushButton("Colour")
		sizeButton = QPushButton("Size")
		saveButton = QPushButton("Save")
		resetButton = QPushButton("Reset")
		controls.addWidget(colourButton)
		controls.addWidget(sizeButton)
		controls.addWidget(saveButton)
		controls.addWidget(resetButton)

		drawSpace = BuildingPainter()
		middleDiv.addWidget(drawSpace)
		middleDiv.addLayout(controls)

		cameraScroll = QScrollArea()
		cameraWidget = QWidget()
		cameraLayout = QVBoxLayout()

		for i in range(0,100):
			cameraLayout.addWidget(QLabel("camera" + str(i)))

		cameraWidget.setLayout(cameraLayout)
		cameraScroll.setWidget(cameraWidget)

		layout.addWidget(levelScroll)
		layout.addLayout(middleDiv)
		layout.addWidget(cameraScroll)


		self.setLayout(layout)

	def begin(self):
		print("Begin")

class BuildingPainter(QFrame):
	def __init__(self):
		QFrame.__init__(self)
		self.setMinimumSize(QSize(700,700))
		self.setFrameStyle(QFrame.Box)
