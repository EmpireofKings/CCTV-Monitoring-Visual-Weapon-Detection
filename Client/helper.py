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

class FeedLoader(Thread):
	#GUI Thread launches this thread
	#to prevent holding GUI Thread for too long keep __init__ minimal
	def __init__(self, feedID):
		Thread.__init__(self)

		self.feedID = feedID

	def setup(self):
		self.feed = cv2.VideoCapture(self.feedID)
		self.FPS = self.feed.get(cv2.CAP_PROP_FPS)

	def run(self):
		global nextFrames
		self.setup()

		timer = time.time()
		while self.feed.isOpened():
			while time.time() - timer < 1/self.FPS : time.sleep(0.01)
			loadCheck, frame = self.feed.read()
			timer = time.time()

			if loadCheck:
				frame = cv2.resize(frame, (640,360))
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

				pmap = QPixmap.fromImage(QImage(frame.data, 640, 360, 3*640,  QImage.Format_RGB888))

				encodeCheck, jpegBuf = cv2.imencode('.jpg', frame)

				if encodeCheck:
					encoded = b64.b64encode(jpegBuf)
					nextFrames[str(self.feedID)] = (pmap, encoded)
			else:
				self.feed.set(cv2.CAP_PROP_POS_FRAMES, 0)


class Networker(Thread):
	def __init__(self, feedID, display):
		Thread.__init__(self)

		self.feedID = feedID
		self.display = display

	def setup(self):
		context = zmq.Context()
		self.socket = context.socket(zmq.REQ)
		self.socket.connect('tcp://localhost:5000')

	def run(self):
		global nextFrames
		self.setup()

		while True:
			frame = nextFrames.get(str(self.feedID))

			if frame is not None:
				self.socket.send(frame[1])

				result = self.socket.recv_string()

				print(result)
				self.display.newFrameSignal.emit(frame[0])

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
