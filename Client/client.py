import numpy as np
import cv2
import sys
import json
import math
from pprint import pprint
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from threading import Thread
import time
import clientLive as cl
import clientHelper as ch
import clientDeferred as cd
from collections import deque

class mainWindow(QMainWindow):
	def __init__(self, helper, sendBuffer):
		QMainWindow.__init__(self)
		items = ["Live Feed", "Existing Media"]

		decision, check = QInputDialog.getItem(self, "Analysis Type", "Please choose", items, editable=False)

		if check == False:
			sys.exit()

		mainWidget = QWidget()

		if decision == items[0]:
			liveAnalyser = cl.LiveAnalysis(helper, sendBuffer)
			mainWidget.setLayout(liveAnalyser.getLayout())
		elif decision == items[1]:
			deferredAnalyser = cd.DeferredAnalysis(helper)
			mainWidget.setLayout(deferredAnalyser.getLayout())

		self.setCentralWidget(mainWidget)

### MAIN ###
if __name__ == '__main__':
	app = QApplication(sys.argv)
	helper = ch.Helper(app)

	sendBuffer = deque()
	mainWindow = mainWindow(helper, sendBuffer)
	mainWindow.show()

	#'35.204.135.105' reserved static ip GCP
	network = ch.Network(sendBuffer, 'localhost', 5000, 5001)
	sendT = Thread(target=network.sendFrames, daemon=True)
	sendT.start()

	sys.exit(app.exec_())
