# Ben Ryan C15507277

import base64 as b64
import copy
import datetime
import json
import logging
import math
import os
import shutil
import sys
import time
from collections import deque
from threading import Thread

import cv2
import ffmpeg
import numpy as np
from PySide2.QtCharts import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtMultimedia import *
from PySide2.QtMultimediaWidgets import *
from PySide2.QtWidgets import *

import _pickle as pickle
import data_handler
from connectors import DisplayConnector, GenericConnector
from feed_loader import FeedLoader
from feed_process_helper import FeedProcessHelper
from networker import Networker
from terminator import Terminator


class DeferredAnalysis(QWidget):
	def __init__(self, app):
		QWidget.__init__(self)
		layout = QHBoxLayout()

		self.supportedImageTypes = (
			'.bmp', '.dib',
			'.jpg', '.jpeg', '.jpe', '.jp2',
			'.png',
			'.webp',
			'.pbm', '.pgm', '.ppm',
			'.sr', '.ras',
			'.tiff', '.tif')

		self.supportedVideoTypes = (
			'.mp4',
			'.m4v',
			'.mkv',
			'.mov',
			'.avi',
			'.wmv',
			'.mpg')

		self.toProcess = []
		self.ready = []

		self.viewer = Viewer(self)
		self.processList = ProcessList(self)
		self.readyList = ReadyList(self)

		layout.addWidget(self.processList)
		layout.addWidget(self.readyList)
		layout.addWidget(self.viewer)

		self.setLayout(layout)

		processHandler = ProcessHandler(self)
		processHandler.setDaemon(True)
		processHandler.start()

	def addFolder(self):
		dialog = QFileDialog()
		path = dialog.getExistingDirectory()

		if path:
			files = os.listdir(path)

			fullPaths = []
			for file in files:
				fullPath = path + '/' + file
				fullPaths.append(fullPath)

			files = self.sortFiles(fullPaths)
			self.addPreviews(files)

	def addFile(self):
		dialog = QFileDialog()
		files = dialog.getOpenFileNames()[0]
		files = self.sortFiles(files)
		self.addPreviews(files)

	def addPreviews(self, files, ready=False):
		images = files.get('images')
		videos = files.get('videos')

		previews = []

		for image in images:
			preview = Preview(self, image=image)
			previews.append(preview)

		for video in videos:
			preview = Preview(self, video=video)
			previews.append(preview)

		if not ready:
			for item in previews:
				self.toProcess.append(item)
			self.updateLists()
		else:
			for item in previews:
				self.ready.append(item)

	def sortFiles(self, files):
		sortedFiles = {
			'images': [],
			'videos': []}

		for file in files:
			if file.endswith(self.supportedImageTypes):
				sortedFiles.get('images').append(file)

			elif file.endswith(self.supportedVideoTypes):
				sortedFiles.get('videos').append(file)

		return sortedFiles

	def updateLists(self):
		self.processList.update()
		self.readyList.update()
		self.viewer.update()
		self.update()

	def moveTop(self, args):
		item = self.toProcess.pop(0)
		itemPath = item.itemPath
		itemType = item.itemType
		previewPmap = item.previewPmap

		previewCopy = Preview(
			self, previewPmap=previewPmap, itemPath=itemPath, itemType=itemType)

		self.ready.insert(0, previewCopy)
		self.updateLists()

	def setupProgressBar(self, args):
		self.processList.progressBar.reset()
		self.processList.progressBar.setMinimum(args[0])
		self.processList.progressBar.setMaximum(args[1])

	def updateProgressBar(self, args):
		self.processList.progressBar.setValue(args[0])


class ProcessHandler(Thread):
	def __init__(self, parent):
		Thread.__init__(self)
		self.parent = parent
		self.terminator = Terminator.getInstance()
		self.moveTopConnector = GenericConnector(self.parent.moveTop)
		self.progressBarSetup = GenericConnector(self.parent.setupProgressBar)
		self.progressBarUpdate = GenericConnector(self.parent.updateProgressBar)

	def run(self):
		while not self.terminator.isTerminating():
			if len(self.parent.toProcess) > 0:
				path = self.parent.toProcess[0].itemPath
				itemType = self.parent.toProcess[0].itemType
				itemName = self.parent.toProcess[0].itemName

				if itemType == 'image':
					img = cv2.imread(path)
					encoded, pmap = self.preprocess(img)

					if encoded is not None:
						networker = Networker(filePath=itemName, imageMode=True)
						networker.setDaemon(True)
						networker.frames.append((encoded, pmap))
						networker.end = True
						networker.start()

						while networker.isAlive():
							time.sleep(0.01)

				elif itemType == 'video':
					networker = Networker(filePath=itemName, deferredMode=True)
					networker.setDaemon(True)
					networker.start()

					feedLoader = FeedLoader(feedID=path, networker=networker)
					feedLoader.setDaemon(True)
					feedLoader.start()

					fps = None
					total = None

					while fps is None or total is None:
						fps, total = feedLoader.getFeedDetails()

					self.progressBarSetup.emitSignal((0, total))

					# wait for video to be finished
					while networker.is_alive():
						self.progressBarUpdate.emitSignal((networker.total,))
						time.sleep(1)

				basePath = '../data/Processed/'
				shutil.copy(path, basePath + itemName)

				self.moveTopConnector.emitSignal()
			time.sleep(2)

	def preprocess(self, frame):
		displaySize = (640, 360)
		processSize = (640, 480)

		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

		displayFrame = cv2.resize(frame, displaySize)
		processFrame = cv2.resize(frame, processSize)

		pmap = QPixmap.fromImage(
			QImage(
				displayFrame.data, displaySize[0],
				displaySize[1], 3 * displaySize[0],
				QImage.Format_RGB888))

		encodeCheck, jpegBuf = cv2.imencode('.jpg', processFrame)

		if encodeCheck:
			encoded = b64.b64encode(jpegBuf)
		else:
			encoded = None

		return encoded, pmap


class ProcessList(QWidget):
	def __init__(self, parent):
		QWidget.__init__(self)
		self.parent = parent
		self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
		self.update()

	def update(self):
		title = QLabel('Queue')
		font = QFont('Helvetica', 18)
		title.setFont(font)
		title.setAlignment(Qt.AlignCenter)
		addFolderButton = QPushButton('Add Folder')
		addFolderButton.clicked.connect(self.parent.addFolder)

		addFileButton = QPushButton('Add File')
		addFileButton.clicked.connect(self.parent.addFile)

		buttonLayout = QHBoxLayout()
		buttonLayout.addWidget(addFolderButton)
		buttonLayout.addWidget(addFileButton)

		listLayout = QVBoxLayout()

		self.progressBar = QProgressBar()

		if len(self.parent.toProcess) > 0:
			p = self.parent.toProcess[0]
			p.setPixmap(
				data_handler.getLabelledPixmap(
					256, 144, "\n\n\n\n\nProcessing...\n                               ", pmap=p.previewPmap))

			p.setStyleSheet("border: 3px solid black")
			listLayout.addWidget(p)

			for preview in self.parent.toProcess[1:]:
				preview.setStyleSheet("border: 3px solid black")
				listLayout.addWidget(preview)
		else:
			pmap = data_handler.getLabelledPixmap(256, 144, "Add Content\n using the buttons above", path='../data/placeholder.png')
			space = QLabel()
			space.setPixmap(pmap)
			space.setStyleSheet("border: 3px solid black")
			listLayout.addWidget(space)

		listWidget = QFrame()
		listWidget.setLayout(listLayout)
		listScroll = QScrollArea()
		listScroll.setWidget(listWidget)

		outerLayout = QVBoxLayout()
		outerLayout.addWidget(title)
		outerLayout.addLayout(buttonLayout)
		outerLayout.addWidget(self.progressBar)
		outerLayout.addWidget(listScroll)

		tempWidget = QWidget()
		tempWidget.setLayout(self.layout())

		self.setLayout(outerLayout)


class ReadyList(QWidget):
	def __init__(self, parent):
		QWidget.__init__(self)
		self.parent = parent
		self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

		files = os.listdir('../data/processed/')

		fullPaths = []
		for file in files:
			fullPath = '../data/processed/' + file
			fullPaths.append(fullPath)

		files = self.parent.sortFiles(fullPaths)
		files = self.parent.addPreviews(files, ready=True)

		self.stopFeedConn = GenericConnector(self.parent.viewer.analyser.resetFeed)

		self.update()

	def update(self):
		title = QLabel('Ready')
		font = QFont('Helvetica', 18)
		title.setFont(font)
		title.setAlignment(Qt.AlignCenter)

		buttonLayout = QHBoxLayout()
		deleteAll = QPushButton('Delete all processed media')
		deleteAll.clicked.connect(self.deleteAll)
		buttonLayout.addWidget(deleteAll)

		listLayout = QVBoxLayout()

		if len(self.parent.ready) > 0:
			for preview in self.parent.ready:
				if self.parent.viewer.analyser.path is not None:
					if os.path.basename(preview.itemPath) == os.path.basename(self.parent.viewer.analyser.path):
						preview.setStyleSheet("border: 3px solid blue")
					else:
						preview.setStyleSheet("border: 3px solid black")
				else:
					preview.setStyleSheet("border: 3px solid black")

				listLayout.addWidget(preview)

		else:
			pmap = data_handler.getLabelledPixmap(256, 144, "Processed Content\n Will Appear Here", path='../data/placeholder.png')
			space = QLabel()
			space.setPixmap(pmap)
			space.setStyleSheet("border: 3px solid black")
			listLayout.addWidget(space)

		listWidget = QFrame()
		listWidget.setLayout(listLayout)
		listScroll = QScrollArea()
		listScroll.setWidget(listWidget)

		filler = QProgressBar()
		sizePolicy = QSizePolicy()
		sizePolicy.setRetainSizeWhenHidden(True)
		filler.setSizePolicy(sizePolicy)

		outerLayout = QVBoxLayout()
		outerLayout.addWidget(title)
		outerLayout.addLayout(buttonLayout)
		outerLayout.addWidget(filler)
		outerLayout.addWidget(listScroll)

		tempWidget = QWidget()
		tempWidget.setLayout(self.layout())

		self.setLayout(outerLayout)

		filler.hide()

	def deleteAll(self):
		self.stopFeedConn.emitSignal()
		time.sleep(1)
		files = os.listdir('../data/processed/')

		for file in files:
			fullPath = '../data/processed/' + file
			os.remove(fullPath)

		self.parent.ready.clear()
		self.update()


class Viewer(QWidget):
	def __init__(self, parent):
		QWidget.__init__(self)
		self.playing = True

		self.title = QLabel()
		font = QFont('Helvetica', 18)
		self.title.setFont(font)
		self.title.setAlignment(Qt.AlignCenter)

		self.surface = QLabel()
		self.placeholder = data_handler.getLabelledPixmap(
			1280, 720, "Click on something in the ready list\nto view it here.",
			path='../data/placeholder.png')
		self.surface.setSizePolicy(QSizePolicy(
			QSizePolicy.Maximum, QSizePolicy.Maximum))
		self.setSizePolicy(QSizePolicy(
			QSizePolicy.Minimum, QSizePolicy.Minimum))

		self.surface.setPixmap(self.placeholder)

		self.timeDisplay = QLabel("0:00:00 / 0:00:00")
		font = QFont('Helvetica', 12)
		self.timeDisplay.setFont(font)

		self.controls = QHBoxLayout()
		self.controls.setAlignment(Qt.AlignCenter)
		self.togglePlay = QPushButton('Play/Pause')
		self.togglePlay.clicked.connect(self.toggle)

		self.togglePlay.setSizePolicy(
			QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))

		self.resultDisplay = QLabel()
		self.resultDisplay.setFont(font)
		self.resultDisplay.setAlignment(Qt.AlignRight)
		self.resultDisplay.setMinimumWidth(50)
		self.resultDisplay.setMaximumWidth(50)

		self.controls.addWidget(self.timeDisplay)
		self.controls.addWidget(self.togglePlay)
		self.controls.addWidget(self.resultDisplay)

		self.analyser = self.Analyser(self)
		self.analyser.setDaemon(True)
		self.analyser.start()

		self.pause = GenericConnector(self.analyser.pausefeed)
		self.play = GenericConnector(self.analyser.playfeed)

		self.chart = self.Chart(self)

		outerLayout = QVBoxLayout()
		outerLayout.addWidget(self.title)
		outerLayout.addWidget(self.surface)
		outerLayout.addLayout(self.controls)
		outerLayout.addWidget(self.chart)

		self.setLayout(outerLayout)

	def toggle(self):
		if self.playing is True:
			self.playing = False
			self.pause.emitSignal()
		else:
			self.playing = True
			self.play.emitSignal()

	def showAnalysis(self, contentType, name):
		# self.analyser.reset()
		self.title.setText(name)
		self.title.update()
		self.analyser.set(contentType, name)

	def updateChart(self, currentFrame):
		self.chart.currentPoint = currentFrame

	def resetChart(self, args):
		if args is not None:
			resultsData, totalFrames, fps = args
			self.chart.maxX = totalFrames
			self.chart.data = resultsData
			self.chart.fps = fps
		else:
			self.chart.maxX = None
			self.chart.data = None
			self.chart.fps = None

		self.chart.update()

	def updateTimeDisplay(self, args):
		cur, total, result = args
		self.timeDisplay.setText(str(cur) + " / " + str(total))
		self.timeDisplay.update()

		percentage = '{:5.2f}'.format(result * 100)
		self.resultDisplay.setText(percentage)
		self.resultDisplay.update()

	def setTitle(self, title):
		self.title.setText(title)

	def updateDisplay(self, frame):
		if isinstance(frame, np.ndarray):
			h, w, c = np.shape(frame)

			pmap = QPixmap.fromImage(
				QImage(
					frame.data, w, h, 3 * w,
					QImage.Format_RGB888))
		else:
			pmap = self.placeholder

		self.surface.setPixmap(pmap)
		self.surface.update()

	class Chart(QLabel):
		def __init__(self, parent):
			QLabel.__init__(self)
			self.data = None
			self.padding = 10
			self.leftPadding = 30
			self.maxX = None
			self.currentPoints = None
			self.closestPoint = None
			self.currentPoint = 0
			self.seek = GenericConnector(parent.analyser.seek)
			self.setMouseTracking(True)
			self.setSizePolicy(QSizePolicy(
				QSizePolicy.Ignored, QSizePolicy.Ignored))

		def paintEvent(self, event):
			if self.data is not None:
				painter = QPainter(self)
				painter.setRenderHint(QPainter.Antialiasing)

				self.top = self.padding
				self.bottom = self.height() - self.padding

				self.left = self.leftPadding  # repeat for readability later
				self.right = self.width() - self.padding

				# Y AXIS
				painter.drawLine(
					self.left, self.bottom,
					self.left, self.top)

				painter.setPen(QColor(0, 0, 255))

				self.currentPoints = []
				count = 0
				for result in self.data:
					pred = result[0]

					yVal = int(self.scale(
						pred, 0, 1, self.bottom, self.top))

					xVal = int(self.scale(
						count, 0, self.maxX, self.left, self.right))
					self.currentPoints.append(QPoint(xVal, yVal))

					count += 1

				painter.drawPolyline(self.currentPoints)

				painter.drawText(self.left - self.leftPadding, self.top, "100%")
				painter.drawText(self.left - self.leftPadding, self.bottom, "    0%")

				painter.setPen(QColor(0, 255, 0))

				xVal = int(self.scale(
					self.currentPoint, 0, self.maxX, self.left, self.right))

				painter.drawLine(xVal, self.bottom, xVal, self.top)

				if self.closestPoint is not None:
					painter.setBrush(QColor(255, 0, 0))
					pen = QPen(QColor(255, 0, 0))
					pen.setWidth(4)
					painter.setPen(pen)
					painter.drawEllipse(self.closestPoint, 2, 2)

					val = self.scale(
						self.closestPoint.y(),
						self.bottom, self.top,
						0, 1)

					val = str(round(val * 100, 2)) + '%'

					font = painter.font()
					font.setPixelSize(14)
					painter.setFont(font)

					textPoint = QPoint(
						self.closestPoint.x() + 5,
						self.closestPoint.y())

					painter.drawText(textPoint, str(val))

		def scale(self, val, inMin, inMax, outMin, outMax):
			return ((val - inMin) / (inMax - inMin)) * (outMax - outMin) + outMin

		def mousePressEvent(self, event):
			if self.data is not None:
				newPos = int(self.scale(event.x(), self.left, self.right, 0, self.maxX))
				self.seek.emitSignal(newPos)

		def mouseMoveEvent(self, event):
			if self.currentPoints is not None:

				dists = []
				for point in self.currentPoints:
					x1 = event.x()
					y1 = event.y()
					x2 = point.x()
					y2 = point.y()

					dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
					dists.append(dist)

				closest = min(dists)
				index = dists.index(closest)

				self.closestPoint = self.currentPoints[index]
				self.update()

	class Analyser(Thread):
		def __init__(self, display):
			Thread.__init__(self)
			self.basePath = '../data/processed/'
			self.path = None
			self.resultPath = None
			self.frameCount = 0
			self.displayConn = DisplayConnector(display)
			self.chartConn = GenericConnector(display.resetChart)
			self.pointConn = GenericConnector(display.updateChart)
			self.timeConn = GenericConnector(display.updateTimeDisplay)
			self.titleConn = GenericConnector(display.setTitle)
			self.reset = False
			self.ready = True
			self.pause = False

		def run(self):
			terminator = Terminator.getInstance()

			while not terminator.isTerminating():
				self.ready = True
				self.chartConn.emitSignal(None)
				self.timeConn.emitSignal(('0:00:00', '0:00:00', 0.0))
				self.displayConn.emitFrame(None)
				self.titleConn.emitSignal('')

				while self.path is None or self.resultPath is None:
					time.sleep(0.01)

				self.titleConn.emitSignal(os.path.basename(self.path))

				self.ready = False
				self.reset = False
				self.feed = cv2.VideoCapture(self.path)

				videoTotal = self.feed.get(cv2.CAP_PROP_FRAME_COUNT)
				fps = self.feed.get(cv2.CAP_PROP_FPS)

				seconds = int(videoTotal / fps)
				vidLength = datetime.timedelta(seconds=seconds)

				resultsFile = open(self.resultPath, 'rb')
				resultsData = pickle.load(resultsFile)[::-1]
				resultsFile.close()

				self.chartConn.emitSignal((resultsData, videoTotal, fps))

				fpsTimer = time.time()
				self.frameCount = 0
				self.lastFrame = -1

				fph = FeedProcessHelper()

				while self.feed.isOpened() and self.reset is False:
					# syncing results index with display frame
					if self.frameCount != self.lastFrame + 1:
						self.feed.set(cv2.CAP_PROP_POS_FRAMES, self.frameCount)
						self.lastFrame = self.frameCount - 1

					if self.feed.get(cv2.CAP_PROP_POS_FRAMES) != self.frameCount:
						self.feed.set(cv2.CAP_PROP_POS_FRAMES, self.frameCount)
						logging.debug('Correcting frame position')

					while time.time() - fpsTimer < 1 / fps or self.pause is True:
						time.sleep(0.01)

					fpsTimer = time.time()
					check, frame = self.feed.read()

					if check:
						results = resultsData[self.frameCount]
						self.frameCount += 1
						self.lastFrame += 1

						classifications = results[0]
						boundingBoxes = results[1]

						regionResults = results[2][0]
						drawCoords = results[2][1]

						fph.drawResults(
							frame, regionResults, drawCoords,
							["Weapon", "Weapon"], invert=True)

						frame = cv2.resize(frame, (1280, 720))
						frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

						if boundingBoxes != []:
							height, width, _ = np.shape(frame)
							for box in boundingBoxes:
								xf, yf, wf, hf = box
								x = int(self.scale(xf, 0, 1, 0, width))
								y = int(self.scale(yf, 0, 1, 0, height))
								w = int(self.scale(wf, 0, 1, 0, width))
								h = int(self.scale(hf, 0, 1, 0, height))

								cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)

						seconds = int(self.frameCount / fps)
						curTime = datetime.timedelta(seconds=seconds)

						self.timeConn.emitSignal((curTime, vidLength, classifications))
						self.displayConn.emitFrame(frame)
						self.pointConn.emitSignal(self.frameCount)
					else:
						self.feed.set(cv2.CAP_PROP_POS_FRAMES, 0)
						self.frameCount = 0
						self.lastFrame = -1

				self.feed.release()

		def scale(self, val, inMin, inMax, outMin, outMax):
			return ((val - inMin) / (inMax - inMin)) * (outMax - outMin) + outMin

		def set(self, contentType, name):
			self.resetFeed()
			self.path = self.basePath + name
			self.resultPath = self.basePath + name + '.result'

		def resetFeed(self):
			self.path = None
			self.resultPath = None
			self.reset = True
			self.pause = False

			while self.ready is False:
				time.sleep(0.001)

		def seek(self, pos):
			self.frameCount = pos

		def pausefeed(self):
			self.pause = True

		def playfeed(self):
			self.pause = False


class Preview(QLabel):
	def __init__(
		self, parent, image=None, video=None, previewPmap=None,
		itemPath=None, itemType=None):
		QLabel.__init__(self)

		self.parent = parent
		displaySize = (256, 144)

		if previewPmap is not None:
			self.itemPath = itemPath
			self.itemType = itemType
			parts = self.itemPath.split('/')
			self.itemName = parts[len(parts) - 1:][0]
			self.previewPmap = previewPmap

		elif image is not None and video is None:
			self.itemPath = image
			self.itemType = 'image'
			parts = self.itemPath.split('/')
			self.itemName = parts[len(parts) - 1:][0]

			image = cv2.imread(image)

			if image is not None:
				image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
				image = cv2.resize(image, displaySize)

				previewPmap = QPixmap.fromImage(
					QImage(
						image.data, displaySize[0],
						displaySize[1], 3 * displaySize[0],
						QImage.Format_RGB888))

		elif image is None and video is not None:
			self.itemPath = video
			self.itemType = 'video'
			parts = self.itemPath.split('/')
			self.itemName = parts[len(parts) - 1:][0]
			feed = cv2.VideoCapture(video)

			frame = np.zeros((256, 144, 3))

			check, frame = feed.read()

			if check:
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				frame = cv2.resize(frame, displaySize)

				previewPmap = QPixmap.fromImage(
					QImage(
						frame.data, displaySize[0],
						displaySize[1], 3 * displaySize[0],
						QImage.Format_RGB888))

				previewPmap = data_handler.getLabelledPixmap(
					256, 144, self.itemName, path=None, pmap=previewPmap)

			feed.release()

		else:
			logging.error('Preview called without file')

		if previewPmap:
			self.previewPmap = previewPmap
			self.setPixmap(previewPmap)

	def mousePressEvent(self, event):
		if self in self.parent.ready:
			self.parent.viewer.showAnalysis(self.itemType, self.itemName)
			self.parent.readyList.update()
			time.sleep(0.1)
