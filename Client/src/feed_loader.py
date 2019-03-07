import cv2
import time
import numpy as np
import base64 as b64
from threading import Thread
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class FeedLoader(Thread):
	#GUI Thread launches this thread
	#to prevent holding GUI Thread for too long keep __init__ minimal
	def __init__(self, camera, networker):
		Thread.__init__(self)

		self.networker = networker
		self.stop = False
		self.camera = camera

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
			while time.time() - timer < 1/self.FPS : time.sleep(0.01)
			loadCheck, frame = self.feed.read()
			timer = time.time()


			if loadCheck:
				# cv2.imshow("frame", frame)
				# cv2.waitKey(1)
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				displayFrame = cv2.resize(frame, displaySize)
				processFrame = cv2.resize(frame, processSize)


				pmap = QPixmap.fromImage(QImage(displayFrame.data, displaySize[0], displaySize[1], 3*displaySize[0],  QImage.Format_RGB888))

				encodeCheck, jpegBuf = cv2.imencode('.jpg', processFrame)

				if encodeCheck:
					encoded = b64.b64encode(jpegBuf)
					self.networker.nextFrame = (encoded, pmap)
			else:
				print("Error loading Frame")
				self.feed.set(cv2.CAP_PROP_POS_FRAMES, 0)

