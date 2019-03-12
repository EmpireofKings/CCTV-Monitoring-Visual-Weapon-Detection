import base64 as b64
import logging
import time
from threading import Thread

import numpy as np

import cv2
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class FeedLoader(Thread):
	# GUI Thread launches this thread
	# to prevent holding GUI Thread for too long keep __init__ minimal
	def __init__(self, camera, networker, display, mainDisplay):
		Thread.__init__(self)

		self.networker = networker
		self.stop = False
		self.camera = camera
		self.displayConn = self.displayConnector(display)
		self.mainDisplayConn = self.displayConnector(mainDisplay)
		self.mainDisplay = mainDisplay

	def run(self):
		displaySize = (640, 360)
		processSize = (256, 144)

		if self.camera.camID.isdigit():
			camID = int(self.camera.camID)
		else:
			camID = self.camera.camID

		feed = cv2.VideoCapture(camID)
		fps = feed.get(cv2.CAP_PROP_FPS)

		timer = time.time()

		while feed.isOpened() and self.stop is False:
			while time.time() - timer < 1 / fps:
				time.sleep(0.01)

			loadCheck, frame = feed.read()
			timer = time.time()

			if loadCheck:
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				displayFrame = cv2.resize(frame, displaySize)
				processFrame = cv2.resize(frame, processSize)

				pmap = QPixmap.fromImage(QImage(
					displayFrame.data, displaySize[0],
					displaySize[1], 3 * displaySize[0], QImage.Format_RGB888))

				encodeCheck, jpegBuf = cv2.imencode('.jpg', processFrame)

				if encodeCheck:
					encoded = b64.b64encode(jpegBuf)
					self.networker.nextFrame = (encoded, pmap)

				self.displayConn.emitFrame(pmap)
			else:
				feed.set(cv2.CAP_PROP_POS_FRAMES, 0)

	class displayConnector(QObject):
		newFrameSignal = Signal(QPixmap)

		def __init__(self, display):
			QObject.__init__(self)
			self.newFrameSignal.connect(display.updateDisplay)

		def emitFrame(self, pmap):
			self.newFrameSignal.emit(pmap)
