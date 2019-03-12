# TODO

import base64 as b64
import json
import logging
import math
import sys
import time
from collections import deque
from pprint import pprint
from threading import Thread

import cv2
import numpy as np
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from data_handler import *
from feed_loader import FeedLoader
from layout_gui import Layout, LayoutMode
from networker import Networker


class LiveAnalysis(QWidget):
	def __init__(self, app, dataLoader):
		QWidget.__init__(self)
		layout = QHBoxLayout()

		dataLoader = DataLoader()
		data = dataLoader.getConfigData()

		drawSpace = Layout(app, data, [LayoutMode.VIEW], self)

		print("HERE : ", type(data), str(data))

		if data[0][0].cameras != []:
			mainDisplay = FeedDisplayer(
				QSize(1280, 720),
				QSize(480, 270),
				data[0][0].cameras[0],
				drawSpace)
		else:
			mainDisplay = FeedDisplayer(
				QSize(1280, 720),
				QSize(480, 270),
				None,
				drawSpace)

		mainDisplayDrawSpace = QVBoxLayout()
		mainDisplayDrawSpace.addWidget(drawSpace)
		mainDisplayDrawSpace.addWidget(mainDisplay)

		layout.addLayout(mainDisplayDrawSpace)

		# Camera monitoring (right side)
		self.cameraView = CameraViewer(app, data, drawSpace, mainDisplay)
		layout.addWidget(self.cameraView)

		self.setLayout(layout)


# ### RIGHT SIDE ###
class CameraViewer(QFrame):
	def __init__(self, app, data, drawSpace, mainDisplay):
		QFrame.__init__(self)

		layout = QVBoxLayout()

		self.gridView = gridViewer(data, drawSpace, mainDisplay)

		scrollArea = QScrollArea()
		scrollArea.setLayout(self.gridView)
		scrollArea.setMinimumSize(QSize(700, 500))

		layout.addWidget(scrollArea)

		self.setLayout(layout)


class gridViewer(QGridLayout):
	def __init__(self, data, drawSpace, mainDisplay):
		QGridLayout.__init__(self)
		self.setSpacing(10)
		self.setMargin(10)

		cameras = []

		for level in data[0]:
			lid = level.levelID

			for camera in level.cameras:
				cameras.append(camera)

		# pprint(cameraIDs)
		# pprint(cameraLocations)
		# layout = QGridLayout()

		maxCols = 3  # TODO, dynamically choose based on availale space
		# figure out how many rows are needed based on amount of items and max cols
		rows = int(math.ceil((len(cameras) / maxCols)))

		count = 0  # item tracker
		for row in range(rows):
			for col in range(maxCols):
				if count < len(cameras):  # more slots than items to fill
					camera = cameras[count]

					# TODO TIDY THIS UP
					feedDisplayer = FeedDisplayer(
						QSize(384, 216), QSize(128, 72), camera, drawSpace, mainDisplay)

					self.addWidget(feedDisplayer, row, col)

					try:
						networker = Networker(camera, feedDisplayer, mainDisplay)
						networker.setDaemon(True)
						networker.start()
						logging.debug('Networker thread started')
					except:
						logging.critical('Networker thread failed to start', exc_info=True)

					try:
						loader = FeedLoader(camera, networker, feedDisplayer, mainDisplay)
						loader.setDaemon(True)
						loader.start()
						logging.debug('Feed loader thread started')
					except:
						logging.critical('Feed loader thread failed to start', exc_info=True)

					count += 1
				else:
					break


class FeedDisplayer(QLabel):
	def __init__(self, maxSize, minSize, camera, drawSpace, mainDisplay=None):
		QLabel.__init__(self)

		# self.setFrameStyle(QFrame.Box)
		self.setMaximumSize(maxSize)
		self.setMinimumSize(minSize)
		self.drawSpace = drawSpace
		self.mainDisplay = mainDisplay

		self.camera = camera

		camLayout = QVBoxLayout()
		camLayout.setMargin(0)
		camLayout.setSpacing(0)

		self.title = QLabel()
		self.title.setMaximumSize(150, 20)
		camLayout.addWidget(self.title)

		self.surface = QLabel()

		camLayout.addWidget(self.surface)

		self.setLayout(camLayout)

	def updateDisplay(self, pmap):
		pmap = pmap.scaled(QSize(self.width(), self.height()), Qt.KeepAspectRatio)
		self.surface.setPixmap(pmap)
		self.title.setText(
			"Level " + str(self.camera.levelID) +
			" " + self.camera.location)

	def mousePressEvent(self, event):
		if self.camera is not None:
			self.drawSpace.controls.setMainFeedID(self.camera)
			self.drawSpace.controls.setLevel(self.camera.levelID)
			if self.mainDisplay is not None:
				self.mainDisplay.camera = self.camera
