import base64 as b64
import logging
import time
from threading import Thread

import numpy as np

import cv2
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from collections import deque
from connectors import DisplayConnector

class FeedLoader(Thread):
	# GUI Thread launches this thread
	# to prevent holding GUI Thread for too long keep __init__ minimal
	def __init__(
		self, camera=None, networker=None, display=None, 
		mainDisplay=None, feedID=None):
		Thread.__init__(self)

		self.networker = networker
		self.stop = False
		self.camera = camera

		if display is not None:
			self.displayConn = DisplayConnector(display)
			self.displayAttached = True
		else:
			self.displayAttached = False

		if mainDisplay is not None:
			self.mainDisplay = mainDisplay
			self.mainDisplayConn = DisplayConnector(mainDisplay)

		self.feedID = feedID
		self.FPS = None
		self.totalFrames = None

	def run(self):
		displaySize = (640, 360)
		processSize = (256, 144)

		if self.camera is not None:
			if self.camera.camID.isdigit():
				camID = int(self.camera.camID)
			else:
				camID = self.camera.camID

			feed = cv2.VideoCapture(camID)
			limitToFPS = True
		elif self.feedID is not None:
			feed = cv2.VideoCapture(self.feedID)
			limitToFPS = False

		if limitToFPS:
			timer = time.time()

		self.FPS = feed.get(cv2.CAP_PROP_FPS)
		self.totalFrames = feed.get(cv2.CAP_PROP_FRAME_COUNT)

		total = 0
		while feed.isOpened() and self.stop is False:
			total += 1
			if limitToFPS:
				while time.time() - timer < 1 / self.FPS:
					time.sleep(0.01)

				timer = time.time()

			loadCheck, frame = feed.read()

			if loadCheck:
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				displayFrame = cv2.resize(frame, displaySize)
				processFrame = cv2.resize(frame, processSize)

				encodeCheck, jpegBuf = cv2.imencode('.jpg', processFrame)

				if encodeCheck:
					encoded = b64.b64encode(jpegBuf)

					if self.feedID is None:
						self.networker.nextFrame = (encoded, displayFrame)
					else:
						while len(self.networker.frames) >= 1000:
							time.sleep(0.01)

						self.networker.frames.append((encoded, displayFrame))

					if self.displayAttached:
						self.displayConn.emitFrame(displayFrame.copy())

			else:
				if self.feedID is None:
					feed.set(cv2.CAP_PROP_POS_FRAMES, 0)
				else:
					break

		self.networker.end = True

	def getFeedDetails(self):
		return self.FPS, self.totalFrames
