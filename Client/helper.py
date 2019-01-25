import numpy as np
import cv2
import sys
import _pickle as pickle
import time
import socket as s
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from threading import Thread
from collections import deque

class FeedLoader(Thread):
	def __init__(self, feedID):
		Thread.__init__(self)

		self.feedID = feedID
		self.feed = cv2.VideoCapture(feedID)
		self.FPS = self.feed.get(cv2.CAP_PROP_FPS)

		self.sendQueue = deque()
		self.sendingThread = FeedSender(('localhost', 5000), self.feedID, self.sendQueue)


	def run(self):
		self.sendingThread.start()

		while self.feed.isOpened():
			check, frame = self.feed.read()

			if check is True:
				frame = cv2.resize(frame, (256,144))
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				_, f1 = cv2.imencode('.jpg', frame)
				#pickled = pickle.dumps(frame)

				print("TYPE:", type(f1))
			self.sendQueue.append(frame)
			#self.toBePaired.append(frame) #for matching with results on return???


class FeedSender(Thread):
	def __init__(self, addr, feedID, sendQueue):
		Thread.__init__(self)

		self.feedID = feedID
		self.sendQueue = sendQueue

		self.socket = s.socket(s.AF_INET, s.SOCK_STREAM)
		self.socket.connect(addr)

		data = (str(feedID).encode('utf-8') + b'END')
		self.socket.send(data)

	def run(self):
		while True:
			if self.sendQueue:
				frame = self.sendQueue.pop() + b'END'

				total = len(frame)
				sent = 0

				while sent < total:
					sent += socket.send(frame[sent:])

				print(self.feedID, "Sent:" , total)

# class FramePack():
# 	def __init__(self, frame, camID):
# 		self.frame = frame
# 		self.camID = camID
#
# 	def getFrameAsndarray(self):
# 		return cv2.imdecode(self.frame)
#
# 	def getFrameAsPixmap(self):
# 		return QPixmap.loadFromData(self.frame)
#
# 	def getCameraID(self):
# 		return self.camID

def getScreenParams(app):
	available = app.primaryScreen().availableGeometry()

	maxHeight = available.height()
	maxWidth = available.width()

	return (maxWidth, maxHeight)
