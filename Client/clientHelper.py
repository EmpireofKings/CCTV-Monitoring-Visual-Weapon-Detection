import numpy as np
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

class FramePack():
	def __init__(self, frame, camID):
		self.frame = frame
		self.camID = camID

	def getFrameAsndarray(self):
		return self.frame

	def getFrameAsQImage(self):
		shape = np.shape(self.frame)
		return QImage(self.frame.data, shape[1], shape[0], QImage.Format_RGB888)

	def getFrameAsPixmap(self):
		image = self.getFrameAsQImage()
		return QPixmap.fromImage(image)

	def getCameraID(self):
		return self.camID
