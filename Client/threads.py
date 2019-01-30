#TODO

import numpy as np
import cv2
import sys
import _pickle as pickle
import time
import zmq
import base64 as b64
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from threading import Thread
from collections import deque

nextFrames = {}
mainFeedID = 0

class FeedLoader(Thread):
	#GUI Thread launches this thread
	#to prevent holding GUI Thread for too long keep __init__ minimal
	def __init__(self, feedData):
		Thread.__init__(self)

		self.stop = False
		self.feedData = feedData

	def setup(self):
		if self.feedData["id"].isdigit():
			self.feed = cv2.VideoCapture(int(self.feedData["id"]))
		else:
			self.feed = cv2.VideoCapture(self.feedData["id"])

		self.FPS = self.feed.get(cv2.CAP_PROP_FPS)

	def run(self):
		global nextFrames
		displaySize = (640, 360)
		processSize = (256, 144)

		self.setup()

		timer = time.time()
		while self.feed.isOpened() and self.stop is False:
			while time.time() - timer < 1/self.FPS : time.sleep(0.01)
			loadCheck, frame = self.feed.read()
			timer = time.time()

			if loadCheck:
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				displayFrame = cv2.resize(frame, displaySize)
				processFrame = cv2.resize(frame, processSize)


				pmap = QPixmap.fromImage(QImage(displayFrame.data, displaySize[0], displaySize[1], 3*displaySize[0],  QImage.Format_RGB888))

				encodeCheck, jpegBuf = cv2.imencode('.jpg', processFrame)

				if encodeCheck:
					encoded = b64.b64encode(jpegBuf)
					nextFrames[str(self.feedData["id"])] = (encoded, pmap)
			else:
				self.feed.set(cv2.CAP_PROP_POS_FRAMES, 0)


class Networker(Thread):
	def __init__(self, feedData, display, mainDisplay):
		Thread.__init__(self)

		self.stop = False
		self.feedData = feedData
		self.display = display
		self.mainDisplay = mainDisplay

	def setup(self):
		serverAddr = 'tcp://35.204.135.105:5000'
		localAddr = 'tcp://127.0.0.1:5000'

		context = zmq.Context()
		self.socket = context.socket(zmq.REQ)
		self.socket.connect(localAddr)

	def run(self):
		global nextFrames
		global mainFeedID
		self.setup()

		while self.stop is False:
			frames = nextFrames.get(str(self.feedData["id"]))

			if frames is not None:
				self.socket.send(frames[0])

				result = self.socket.recv_string()
				#print(self.feedID, result)

				self.display.newFrameSignal.emit(frames[1])

				#if this display is the main, emit the frame signal to both displays
				if self.feedData["id"] == mainFeedID:
					self.mainDisplay.newFrameSignal.emit(frames[1])
					self.mainDisplay.feedData = self.feedData

def getScreenParams(app):
	available = app.primaryScreen().availableGeometry()

	maxHeight = available.height()
	maxWidth = available.width()

	return (maxWidth, maxHeight)
