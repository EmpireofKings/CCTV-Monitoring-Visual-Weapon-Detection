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
from PySide2.QtMultimedia import *

from data_handler import *
from feed_loader import FeedLoader
from layout_gui import Layout, LayoutMode
from networker import Networker
from gtts import gTTS
import uuid
from terminator import Terminator
from notify_run import Notify
from connectors import GenericConnector


class LiveAnalysis(QWidget):
	def __init__(self, app, dataLoader):
		QWidget.__init__(self)
		layout = QHBoxLayout()

		dataLoader = DataLoader()
		data = dataLoader.getConfigData()

		if data[0] != []:
			self.levelMenu = None
			self.cameraMenu = None

			self.drawSpace = Layout(app, data, [LayoutMode.VIEW], self)

			self.drawSpace.painter.setMinimumSize(600, 600)

			self.drawSpace.painter.setSizePolicy(QSizePolicy(
				QSizePolicy.Fixed, QSizePolicy.Fixed))

			self.drawSpace.controls.setSizePolicy(QSizePolicy(
				QSizePolicy.Minimum, QSizePolicy.Fixed))

			if data[0][0].cameras != []:
				mainDisplay = FeedDisplayer(
					data[0][0].cameras[0],
					self.drawSpace,
					minSize=QSize(640, 360))
			else:
				mainDisplay = FeedDisplayer(
					None,
					self.drawSpace,
					minSize=QSize(640, 360))

			mainDisplayDrawSpace = QVBoxLayout()
			mainDisplayDrawSpace.addWidget(self.drawSpace)
			mainDisplayDrawSpace.addWidget(mainDisplay)

			layout.addLayout(mainDisplayDrawSpace)

			# Camera monitoring (right side)
			self.cameraView = CameraViewer(app, data, self.drawSpace, mainDisplay, self)
			layout.addWidget(self.cameraView)

			self.dialog = AlertDialog()

			alertWatcher = AlertWatcher(self)
			alertWatcher.setDaemon(True)
			alertWatcher.start()
		else:
			message = QLabel(
				'No live configuration data found.\nUse the configuration tab begin.')
			font = QFont('Helvetica', 24)
			message.setFont(font)
			message.setAlignment(Qt.AlignCenter)
			layout.addWidget(message)

		self.setLayout(layout)

	def updateLayout(self):
		self.drawSpace.painter.update()

	def showAlertDialog(self, msg):
		self.dialog.detected.setText(msg)
		self.dialog.exec_()


class AlertDialog(QDialog):
	def __init__(self):
		QDialog.__init__(
			self, None,
			Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

		self.banner = QLabel()
		pmap = getPixmap(640, 360, '../data/icons/attention.png', keepAspect=True)
		self.banner.setPixmap(pmap)

		self.detected = QLabel()
		font = QFont('Helvetica', 10)
		self.detected.setFont(font)

		outerLayout = QVBoxLayout()
		outerLayout.addWidget(self.banner)
		outerLayout.addWidget(self.detected)

		self.setLayout(outerLayout)


class AlertWatcher(Thread):
	def __init__(self, parent):
		Thread.__init__(self)
		self.parent = parent
		self.updateLayout = GenericConnector(self.parent.updateLayout)
		self.alertDialog = GenericConnector(self.parent.showAlertDialog)

		self.index = {}
		self.playlist = []

		soundsPath = '../data/Sounds'
		files = os.listdir(soundsPath)

		fullPaths = []

		for file in files:
			path = soundsPath + '/' + file
			fullPaths.append(path)

		count = 0
		for file in fullPaths:
			media = QUrl.fromLocalFile(file)
			self.playlist.append(media)
			self.index[file] = count
			count += 1

		self.player = QMediaPlayer()
		self.player.stateChanged.connect(self.mediaStateChange)
		self.finished = True

		self.soundsPath = '../data/Sounds'
		self.detectedPath = soundsPath + '/weapondetected.mp3'
		self.andPath = soundsPath + '/and.mp3'
		self.notify = Notify()


	def run(self):
		terminator = Terminator.getInstance()

		while not terminator.isTerminating():
			currentDisplayData = self.parent.drawSpace.painter.data[0]

			soundsToPlay = []
			msg = 'Locations Detected:'
			for level in currentDisplayData:
				lvlMsg = '\n\tLevel ' + str(level.levelID)
				camMsgs = ''
				for camera in level.cameras:
					if camera.alert is True:
						if camera.alerted is False:
							self.parent.drawSpace.controls.setMainFeedID(camera)
							camera.alerted = True
							soundsToPlay.append(camera.soundPath)

							alertMsg = ('Weapon detected at level ' +
									str(camera.levelID) + ' ' +
									camera.location)

							alerter = Thread(target=self.sendAlert, args=[alertMsg])
							alerter.start()

						camMsgs += '\n\t\t' + camera.location
					elif camera.alerted is True:
						camera.alerted = False
				if camMsgs != '':
					msg += lvlMsg + camMsgs + '\n'

			if len(soundsToPlay) > 0:
				self.alertDialog.emitSignal(msg)
				self.playUntilDone(self.playlist[self.index.get(self.detectedPath)])

			count = 0
			for path in soundsToPlay:
				print(path)
				print(self.index)
				print(self.index.get(path))

				self.playUntilDone(self.playlist[self.index.get(path)])

				if count == len(soundsToPlay) - 2:
					self.playUntilDone(self.playlist[self.index.get(self.andPath)])

				count += 1

			time.sleep(0.1)

	def sendAlert(self, msg):
		self.notify.send(msg)

	def playUntilDone(self, media):
		self.finished = False
		self.player.setMedia(media)
		self.player.play()

		while not self.finished:
			time.sleep(0.01)

	def mediaStateChange(self, state):
		if state == QMediaPlayer.StoppedState:
			self.finished = True

# ### RIGHT SIDE ###
class CameraViewer(QFrame):
	def __init__(self, app, data, drawSpace, mainDisplay, parent):
		QFrame.__init__(self)

		layout = QVBoxLayout()

		self.gridView = gridViewer(data, drawSpace, mainDisplay, parent)

		scrollArea = QScrollArea()
		scrollArea.setLayout(self.gridView)
		scrollArea.setMinimumSize(QSize(700, 500))

		layout.addWidget(scrollArea)

		self.setLayout(layout)


class gridViewer(QGridLayout):
	def __init__(self, data, drawSpace, mainDisplay, parent):
		QGridLayout.__init__(self)
		self.setSpacing(10)
		self.setMargin(10)
		self.parent = parent

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

		soundsPath = '../data/Sounds'
		if not os.path.exists(soundsPath):
			os.mkdir(soundsPath)

		detectedPath = soundsPath + '/weapondetected.mp3'
		if not os.path.exists(detectedPath):
			detectedSound = gTTS('Weapon detected on')
			detectedSound.save(detectedPath)
		else:
			logging.debug('Starter sound already exists at %s', detectedPath)

		andPath = soundsPath + '/and.mp3'
		if not os.path.exists(andPath):
			andSound = gTTS('and')
			andSound.save(andPath)
		else:
			logging.debug('And sound already exists at %s', andPath)

		count = 0  # item tracker
		for row in range(rows):
			for col in range(maxCols):
				if count < len(cameras):  # more slots than items to fill
					camera = cameras[count]

					alertText = (
						"Level " + str(camera.levelID) + camera.location)

					path = soundsPath + '/' + alertText.replace(' ', '') + '.mp3'

					camera.soundText = alertText
					camera.soundPath = path

					if not os.path.exists(path):
						alertAudio = gTTS(alertText)
						alertAudio.save(path)

					feedDisplayer = FeedDisplayer(
						camera, drawSpace, mainDisplay, 
						maxSize=QSize(384, 216), minSize=QSize(128, 72),
						parent = self.parent)

					feedDisplayer.surface.setStyleSheet("border: 3px solid black")

					self.addWidget(feedDisplayer, row, col)

					try:
						networker = Networker(
							camera=camera, display=feedDisplayer,
							mainDisplay=mainDisplay, layoutHandler=parent)
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
	def __init__(self, camera, drawSpace, mainDisplay=None, maxSize=None, minSize=None, parent=None):
		QLabel.__init__(self)
		self.parent = parent

		if maxSize is not None:
			self.setMaximumSize(maxSize)

		if minSize is not None:
			self.setMinimumSize(minSize)

		self.setSizePolicy(QSizePolicy(
			QSizePolicy.Minimum, QSizePolicy.Minimum))

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

	def updateDisplay(self, frame):
		displaySize = (640, 360)

		pmap = QPixmap.fromImage(
					QImage(
						frame.data, displaySize[0],
						displaySize[1], 3 * displaySize[0],
						QImage.Format_RGB888))

		pmap = pmap.scaled(QSize(self.width(), self.height()), Qt.KeepAspectRatio)
		self.surface.setPixmap(pmap)
		self.title.setText(
			"Level " + str(self.camera.levelID) +
			" " + self.camera.location)

		if self.parent is not None:
			selectedCam = self.parent.drawSpace.controls.getSelectedCamera()
			if selectedCam is not None:
				if selectedCam.camID == self.camera.camID:
					self.surface.setStyleSheet("border: 3px solid blue")
				else:
					self.surface.setStyleSheet("border: 3px solid black")

	def mousePressEvent(self, event):
		if self.camera is not None:
			self.drawSpace.controls.setMainFeedID(self.camera)
			self.drawSpace.controls.setLevel(self.camera.levelID)
			if self.mainDisplay is not None:
				self.mainDisplay.camera = self.camera
