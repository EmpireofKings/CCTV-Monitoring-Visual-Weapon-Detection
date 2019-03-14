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
from PySide2.QtMultimedia import *
from PySide2.QtMultimediaWidgets import *
from threading import Thread
import time
import logging
from collections import deque
import os
from terminator import Terminator
import copy
from networker import Networker
from feed_loader import FeedLoader
import base64 as b64
import ffmpeg
import shutil
import data_handler


class DeferredAnalysis(QWidget):
	def __init__(self, app):
		QWidget.__init__(self)
		layout = QHBoxLayout()

		self.toProcess = []
		self.ready = []

		self.processList = ProcessList(self)
		self.readyList = ReadyList(self)
		self.viewer = Viewer(self)

		layout.addWidget(self.processList)
		layout.addWidget(self.readyList)
		layout.addWidget(self.viewer)

		self.setLayout(layout)

		processHandler = ProcessHandler(self)
		processHandler.setDaemon(True)
		processHandler.start()

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
			'.webm',
			'.mov',
			'.avi',
			'.wmv',
			'.mpg',
			'.flv')

	def addFolder(self):
		dialog = QFileDialog()
		path = dialog.getExistingDirectory()

		if path:
			logging.debug('Chosen Folder %s', path)
			files = os.listdir(path)

			fullPaths = []
			for file in files:
				fullPath = path + '/' + file
				fullPaths.append(fullPath)

			files = self.sortFiles(fullPaths)
			self.addPreviews(files)

	def addFile(self):
		dialog = QFileDialog()
		path, check = dialog.getOpenFileName()

		if check:
			logging.debug('Chosen File %s', path)
			file = self.sortFiles([path])
			self.addPreviews(file)

	def addPreviews(self, files):
		images = files.get('images')
		videos = files.get('videos')

		for image in images:
			preview = Preview(self, image=image)
			self.toProcess.append(preview)

		for video in videos:
			preview = Preview(self, video=video)
			self.toProcess.append(preview)

		self.updateLists()

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
		self.processList.progressBar.show()

	def updateProgressBar(self, args):
		self.processList.progressBar.setValue(args[0])


class ProcessHandler(Thread):
	def __init__(self, parent):
		Thread.__init__(self)
		self.parent = parent
		self.terminator = Terminator.getInstance()
		self.moveTopConnector = self.UpdateConnector(self.parent.moveTop)
		self.progressBarSetup = self.UpdateConnector(self.parent.setupProgressBar)
		self.progressBarUpdate = self.UpdateConnector(self.parent.updateProgressBar)

	def run(self):
		while not self.terminator.isTerminating():
			if len(self.parent.toProcess) > 0:
				path = self.parent.toProcess[0].itemPath
				itemType = self.parent.toProcess[0].itemType
				itemName = self.parent.toProcess[0].itemName

				if itemType == 'image':
					pass
					# img = cv2.imread(path)
					# encoded, pmap = self.preprocess(img)

					# if encoded is not None:
					# 	self.networker.nextFrame = (encoded, pmap)

					# 	while self.networker.deferredFrameResult is None:
					# 		time.sleep(0.01)

					# 	result = copy.copy(self.networker.deferredFrameResult)
					# 	self.networker.deferredFrameResult = None

					# 	self.saveProcessed(image=img, results=result, name=itemName)

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

					basePath = '../Processed/'
					shutil.copy(path, basePath + itemName)

					# wait for video to be finished
					while networker.is_alive():
						self.progressBarUpdate.emitSignal((networker.total,))
						time.sleep(1)

				self.moveTopConnector.emitSignal()
			time.sleep(2)

	def preprocess(self, frame):
		displaySize = (640, 360)
		processSize = (256, 144)

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

	def saveProcessed(self, name, results, image=None):
		basePath = '../Processed/'
		impath = basePath + name
		respath = basePath + 'results-' + name + '.txt'

		if image is not None:
			cv2.imwrite(impath, image)

		with open(respath, 'w') as fp:
			fp.write(str(results))

	class UpdateConnector(QObject):
		moveTopSignal = Signal(tuple)

		def __init__(self, func):
			QObject.__init__(self)
			self.moveTopSignal.connect(func)

		def emitSignal(self, args=None):
			self.moveTopSignal.emit(args)


class ProcessList(QWidget):
	def __init__(self, parent):
		QWidget.__init__(self)
		self.parent = parent
		self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
		self.update()


	def update(self):
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
					256, 144, "Processing...", pmap=p.previewPmap))

			listLayout.addWidget(p)

			for preview in self.parent.toProcess[1:]:
				listLayout.addWidget(preview)
		else:
			pmap = data_handler.getLabelledPixmap(256, 144, "Add Content\n using the buttons above", path='../data/placeholder.png')
			space = QLabel()
			space.setPixmap(pmap)
			listLayout.addWidget(space)

		listWidget = QFrame()
		listWidget.setFrameStyle(QFrame.Box)
		listWidget.setLayout(listLayout)
		listScroll = QScrollArea()
		listScroll.setWidget(listWidget)

		outerLayout = QVBoxLayout()
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
		self.update()


	def update(self):
		listLayout = QVBoxLayout()

		if len(self.parent.ready) > 0:
			for preview in self.parent.ready:
				listLayout.addWidget(preview)
		else:
			pmap = data_handler.getLabelledPixmap(256, 144, "Processed Content\n Will Appear Here", path='../data/placeholder.png')
			space = QLabel()
			space.setPixmap(pmap)
			listLayout.addWidget(space)

		listWidget = QFrame()
		listWidget.setFrameStyle(QFrame.Box)
		listWidget.setLayout(listLayout)
		listScroll = QScrollArea()
		listScroll.setWidget(listWidget)

		outerLayout = QVBoxLayout()
		outerLayout.addWidget(listScroll)

		tempWidget = QWidget()
		tempWidget.setLayout(self.layout())

		self.setLayout(outerLayout)


class Viewer(QWidget):
	def __init__(self, parent):
		QWidget.__init__(self)

		path1 = 'D:/CompSci/College/Year4/FinalYearProject/Semester2/Dev/Client/data/videos/0.mp4'
		path2 = 'D:/Data/Videos/Movies/2001.aso.1080p-mnnkps.mkv'
		path3 = 'D:/CompSci/College/Year4/FinalYearProject/Semester2/Dev/Client/data/videos/bird.avi'
		path4 = 'D:/CompSci/College/Year4/FinalYearProject/Semester2/Dev/Client/data/videos/SampleVideo_1280x720_30mb.flv'
		path5 = 'D:/CompSci/College/Year4/FinalYearProject/Semester2/Dev/Client/data/videos/file_example_WMV_1920_9_3MB.wmv'
		url = QUrl.fromLocalFile(path5)
		content = QMediaContent(url)

		print(str(url))

		self.playlist = QMediaPlaylist()
		self.playlist.addMedia(content)
		self.playlist.setCurrentIndex(1)

		self.player = QMediaPlayer()
		self.player.setPlaylist(self.playlist)

		self.display = QVideoWidget()
		self.display.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
		self.player.setVideoOutput(self.display)

		outerLayout = QVBoxLayout()
		outerLayout.addWidget(self.display)

		self.player.play()
		self.setLayout(outerLayout)


class Preview(QLabel):
	def __init__(
		self, parent, image=None, video=None, previewPmap=None,
		itemPath=None, itemType=None):

		QLabel.__init__(self)
		displaySize = (256, 144)
		self.setFrameStyle(QFrame.Box)

		if previewPmap is not None:
			self.itemPath = itemPath
			self.itemType = itemType
			self.previewPmap = previewPmap

		elif image is not None and video is None:
			self.itemPath = image
			self.itemType = 'image'

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
			feed = cv2.VideoCapture(video)

			frame = np.zeros((256, 144, 3))

			while feed.isOpened() and np.mean(frame) < 50:
				check, frame = feed.read()

				if check:
					frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
					frame = cv2.resize(frame, displaySize)

					previewPmap = QPixmap.fromImage(
						QImage(
							frame.data, displaySize[0],
							displaySize[1], 3 * displaySize[0],
							QImage.Format_RGB888))

			feed.release()

		else:
			logging.error('Preview called without file')

		if previewPmap:
			self.previewPmap = previewPmap
			self.setPixmap(previewPmap)

			parts = self.itemPath.split('/')
			self.itemName = parts[len(parts) - 1:][0]

	def mousePressEvent(self, event):
		logging.debug('Path %s, type %s', self.itemPath, self.itemType)
