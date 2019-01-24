import numpy as np
import cv2
import sys
import _pickle as pickle
import time
import socket as s
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

### HELPER FUNCTION/CLASSES ###
class Helper():
	def __init__(self, app):
		self.PrimaryScreen = app.primaryScreen()

	def getScreenParams(self):
		available = self.PrimaryScreen.availableGeometry()

		maxHeight = available.height()
		maxWidth = available.width()

		return (maxWidth, maxHeight)

	### THREAD FUNCTIONS ###
	def loadThread(self, sendBuffer, size, id):
		feed = cv2.VideoCapture(id)

		while feed.isOpened():
			check, frame = feed.read()

			if check == True:
				frame = cv2.resize(frame, size)
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

				frame = cv2.imencode('.jpg', frame)
				fp = FramePack(frame, id)
				serialized = b'IMAGE_BORDER'+pickle.dumps(fp)+b'IMAGE_BORDER'
				sendBuffer.append(serialized)
				#print(len(sendBuffer))
			else:
				feed.set(cv2.CAP_PROP_POS_FRAMES, 0)

	def displayThread(self, display, size, id):
		return
		# feed = cv2.VideoCapture(id)
		# vidFPS = feed.get(cv2.CAP_PROP_FPS)
		#
		# cur = time.time()
		# while((time.time() - cur) < 1/vidFPS) :time.sleep(0.01)
		#
		# display.newFrameReady(fp1)

class Network():
	def __init__(self, sendBuffer, HOST, UPPORT, DOWNPORT):
		self.sendBuffer = sendBuffer
		self.upSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
		self.upSocket.connect((HOST, UPPORT))

		self.downSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
		self.downSocket.connect((HOST, DOWNPORT))

	def sendFrames(self):
		while True:
			curSize = len(self.sendBuffer)

			buffer = b''
			for _ in range(curSize):
				buffer += deque.pop()

			sent = 0
			total = len(buffer)

			while(sent < buffer):
				total += self.upSocket.send(buffer[total:])

	def recvFrames(self):
		return

class FramePack():
	def __init__(self, frame, camID):
		self.frame = frame
		self.camID = camID

	def getFrameAsndarray(self):
		return cv2.imdecode(self.frame)

	def getFrameAsPixmap(self):
		return QPixmap.loadFromData(self.frame)

	def getCameraID(self):
		return self.camID
