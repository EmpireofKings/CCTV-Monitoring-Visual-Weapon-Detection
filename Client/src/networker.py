import zmq
from threading import Thread
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Networker(Thread):
	def __init__(self, camera, display, mainDisplay):
		Thread.__init__(self)

		self.stop = False
		self.camera = camera
		self.display = display
		self.nextFrame = None
		self.mainDisplay = mainDisplay

	def setup(self):
		serverAddr = 'tcp://35.204.135.105'
		localAddr = 'tcp://127.0.0.1'
		initPort = ':5000'

		context = zmq.Context()
		initSocket = context.socket(zmq.REQ)
		initSocket.connect(localAddr + initPort)

		initSocket.send_string(str(self.camera.id))

		mainPort = ':' + initSocket.recv_string()

		self.socket = context.socket(zmq.REQ)
		self.socket.connect(localAddr + mainPort)

	def run(self):
		global mainFeedID
		self.setup()

		while self.stop is False:
			if self.nextFrame is not None:
				frames = self.nextFrame

				self.socket.send(frames[0])

				result = self.socket.recv_string()
				# print(self.camera.id, result)

				# self.display.newFrameSignal.emit(frames[1])

				# uf this display is the main, emit the frame signal to both displays
				# if self.camera.id == self.mainDisplay.camera.id:
				# 	self.mainDisplay.newFrameSignal.emit(frames[1])
				# 	self.mainDisplay.camera = self.camera
