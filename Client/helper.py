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
		while self.feed.isOpened():
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

		while True:
			frames = nextFrames.get(str(self.feedData["id"]))

			if frames is not None:
				self.socket.send(frames[0])

				result = self.socket.recv_string()
				#print(self.feedID, result)

				self.display.newFrameSignal.emit(frames[1])

				#if this display is the main, emit the frame signal to both displays
				if self.feedData["id"] == mainFeedID:
					self.mainDisplay.newFrameSignal.emit(frames[1])

#
# sendFrame = None
# class FeedSender(Thread):
# 	def __init__(self, addr, feedID, sendQueue, display):
# 		Thread.__init__(self)
#
# 		self.addr = addr
# 		self.display = display
# 		self.feedID = feedID
# 		self.sendQueue = sendQueue
#
# 	def run(self):
# 		self.socket = s.socket(s.AF_INET, s.SOCK_STREAM)
# 		self.socket.connect(self.addr)
#
# 		data = (str(self.feedID).encode('utf-8') + b'RecvEND')
# 		self.socket.send(data)
#
# 		global sendFrame
# 		while True:
# 			if sendFrame is not None:
# 				print("HRER")
# 				frame = sendFrame
# 				sendFrame = None
# 				#print(frame[len(frame)-20:])
#
# 				total = len(frame)
# 				sent = 0
#
# 				while sent < total:
# 					sent += self.socket.send(frame[sent:])
#
# 				self.display.newFrameReady(pickle.loads(frame))
#
# 				#print(self.feedID, "Sent:" , total)
#
# class FeedReceiver(Thread):
# 	def __init__(self, addr, feedID, display):
# 		Thread.__init__(self)
# 		self.feedID = feedID
# 		self.displayQueue = deque()
#
# 	def run(self):
# 		self.socket = s.socket(s.AF_INET, s.SOCK_STREAM)
# 		self.socket.connect(addr)
#
# 		data = (str(feedID).encode('utf-8') + b'RespEND')
# 		self.socket.send(data)
#
# 		displayer = FeedDisplayer(self.feedID, display, self.displayQueue)
# 		displayer.setDaemon(True)
# 		displayer.start()
#
# 		overflow = None
# 		while self.socket is not None:
# 			data = b''
#
# 			if overflow is not None:
# 				data = overflow
# 				overflow = None
#
# 			while True:
# 				data += self.socket.recv(8096)
#
# 				if b'\x94t\x94b.' in data:
# 					index = data.index(b'\x94t\x94b.')
# 					overflow = data[index+len('\x94t\x94b.'):]
# 					data = data[:index+len('\x94t\x94b.')]
# 					break
#
# 			self.displayQueue.append(data)
#
# class FeedDisplayer(Thread):
# 	def __init__(self, feedID, display, queue):
# 		Thread.__init__(self)
#
# 		self.feedID = feedID
# 		self.display = display
# 		self.queue = queue
#
# 	def run(self):
# 		while True:
# 			if self.queue:
# 				frame = getFrameAsPixmap(self.feedID, self.queue.pop())
#
# 				# if frame is not None:
# 				# 	self.display.newFrameReady(frame)
#
# def getFrameAsPixmap(feedID, frame):
# 	frame = pickle.loads(frame)
# 	h, w, c = np.shape(frame)
# 	# print(shape, np.mean(frame))
# 	# if len(shape) == 0:
# 	# 	return None
#
# 	# cv2.imshow("frame", frame)
# 	# cv2.waitKey(0)
#
# 	frame = QImage(frame.data, w, h, c*w,  QImage.Format_RGB888)
# 	return QPixmap.fromImage(frame)

def getScreenParams(app):
	available = app.primaryScreen().availableGeometry()

	maxHeight = available.height()
	maxWidth = available.width()

	return (maxWidth, maxHeight)
