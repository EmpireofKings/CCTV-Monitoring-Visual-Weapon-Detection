import base64 as b64
import time
from threading import Thread

import numpy as np

import cv2
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class displayConnector(QObject):
		newFrameSignal = Signal(QPixmap)

		def __init__(self, display):
			QObject.__init__(self)
			self.newFrameSignal.connect(display.updateDisplay)

		def emitFrame(self, pmap):
			self.newFrameSignal.emit(pmap)


class FeedLoader(Thread):
	# GUI Thread launches this thread
	# to prevent holding GUI Thread for too long keep __init__ minimal
	def __init__(self, camera, networker, display, mainDisplay):
		Thread.__init__(self)

		self.networker = networker
		self.stop = False
		self.camera = camera
		self.displayConn = displayConnector(display)
		self.mainDisplayConn = displayConnector(mainDisplay)
		self.mainDisplay = mainDisplay

	def setup(self):
		if self.camera.id.isdigit():
			self.feed = cv2.VideoCapture(int(self.camera.id))
		else:
			self.feed = cv2.VideoCapture(self.camera.id)

		self.FPS = self.feed.get(cv2.CAP_PROP_FPS)

	def run(self):
		displaySize = (640, 360)
		processSize = (256, 144)

		self.setup()

		timer = time.time()
		while self.feed.isOpened() and self.stop is False:
			while time.time() - timer < 1 / self.FPS:
				time.sleep(0.01)

			loadCheck, frame = self.feed.read()
			timer = time.time()

			if loadCheck:
				# cv2.imshow(str(self.camera.id), frame)
				# cv2.waitKey(0)
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

				# self.displayConn.emitFrame(pmap)

				# # if this display is the main, emit the frame signal to both displays
				# if self.camera.id == self.mainDisplay.camera.id:
				# 	self.mainDisplayConn.emitFrame(pmap)

			else:
				self.feed.set(cv2.CAP_PROP_POS_FRAMES, 0)
