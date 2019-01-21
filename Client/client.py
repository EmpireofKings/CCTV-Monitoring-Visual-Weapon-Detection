import numpy as np
import cv2
import sys
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class mainWindow(QMainWindow):
	def __init__(self):
		QMainWindow.__init__(self)
		items = ["Live Feed", "Existing Media"]
		decision = QInputDialog.getItem(self, "Analysis Type", "Please choose", items, editable=False)

		mainWidget = QWidget()

		if decision[0] == items[0]:
			layout = self.initLive()
			mainWidget.setLayout(layout)
		elif decision[0] == items[1]:
			mainWidget.setLayout(initExis())

		self.setCentralWidget(mainWidget)

	def initLive(self):
		layout = QHBoxLayout()

		#System Overview (left side)
		overviewLayout = QVBoxLayout()
		buildingView = BuildingPainter()


		optionsPlaceholder = QLabel("Level: 1 2 3 4 5 6 ... placeholder")

		overviewLayout.addWidget(buildingView)
		overviewLayout.addWidget(optionsPlaceholder)

		layout.addLayout(overviewLayout)

		#Camera monitoring (right side)
		cameraLayout = QVBoxLayout()
		camPreviewLayout = QGridLayout()
		cameraPlaceholder = QLabel("Cameras placeholder")
		camPreviewLayout.addWidget(cameraPlaceholder,1 , 1)

		mainCamPlaceholder = QLabel("Main Cam placeholder")

		cameraLayout.addLayout(camPreviewLayout)
		cameraLayout.addWidget(mainCamPlaceholder)

		layout.addLayout(cameraLayout)

		return layout

	def initExis(self):
		layout = None
		#TODO: Setup existing media analysis layout
		return layout

class BuildingPainter(QWidget):
	def __init__(self):
		QWidget.__init__(self)
		self.setMinimumSize(QSize(500,500))
		self.levels = [QRect(100,100,100,100), QRect(300,300,100,100)]
		self.currentLevel = self.levels[1]
		#PAINT BUILDING

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.drawRect(self.currentLevel)

	def mousePressEvent(self, event):
		self.currentLevel = self.levels[0]
		self.repaint()

if __name__ == '__main__':
	app = QApplication(sys.argv)
	mainWindow = mainWindow()
	mainWindow.show()
	sys.exit(app.exec_())
