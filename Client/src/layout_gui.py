from enum import Enum
import math

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from data_handler import *

class LayoutMode(Enum):
	VIEW = 1
	EDIT = 2

class Layout(QFrame):
	def __init__(self, app, data, modes, config):
		QFrame.__init__(self)
		self.data = data
		self.setFrameStyle(QFrame.Box)
		self.setMinimumSize(QSize(700,700))

		self.painter = LayoutPainter(app, data, modes)
		self.controls = LayoutControls(app, data, modes, self.painter, config)

		layout = QVBoxLayout()
		layout.addWidget(self.painter)
		layout.addWidget(self.controls)

		self.setLayout(layout)


class LayoutPainter(QFrame):
	def __init__(self, app, data, modes):
		QFrame.__init__(self)
		self.data = data
		self.currentLevel = 0
		self.mainFeedID = '0'

		self.levelIDs = []

		for level in self.data:
			self.levelIDs.append(level.id)

		self.tooltip = QToolTip()

		self.setMinimumSize(QSize(700, 300))
		#self.setMaximumSize(QSize(700, 300))

		self.setMouseTracking(True)

	def paintEvent(self, event):
		painter = QPainter(self)

		if self.data != []:
			self.levelIDs.sort()
			index = self.levelIDs.index(int(self.currentLevel))
			self.level = self.data[index]

			self.currentpmap = getPixmap(self.width(), self.height(), self.level.drawPath)
			pmapDrawX = (self.width() - self.currentpmap.width()) / 2

			painter.drawPixmap(QPoint(pmapDrawX,0), self.currentpmap)
			#print(self.width(), self.height(), self.currentpmap.width(), self.currentpmap.height())

			for camera in self.level.cameras:
				camX = self.range2range(camera.position.x(), 0, 500, 0, self.currentpmap.width() + pmapDrawX)
				camY = self.range2range(camera.position.y(), 0,500, 0, self.currentpmap.height())

				painter.setPen(camera.color)
				painter.setBrush(QBrush(camera.color, Qt.SolidPattern))


				radius = 20
				arrowX = int((radius * math.sin(math.radians(camera.angle)))) + camX
				arrowY = int((radius * math.cos(math.radians(camera.angle)))) + camY
				arrowPoint = QPoint(arrowX, arrowY)

				painter.drawEllipse(QPoint(camX, camY), camera.size, camera.size)
				painter.drawLine(QPoint(camX, camY), arrowPoint)

				if camera.id == self.mainFeedID:
					painter.setBrush(Qt.NoBrush)
					pen = QPen(QColor(0, 255, 0))
					pen.setWidth(3)
					painter.setPen(pen)
					painter.drawEllipse(QPoint(camX, camY), camera.size, camera.size)

	def mousePressEvent(self, event):
		if self.data != []:
			id = self.getCloseCam(event.x(), event.y())

			if id is not None:
				self.mainFeedID = id
				self.repaint()

	def mouseMoveEvent(self, event):
		if self.data != []:
			pos = event.globalPos()
			id = self.getCloseCam(event.x(), event.y())

			if id is not None:
				self.tooltip.showText(pos, str(id))

	def getCloseCam(self, x1, y1):
		if self.level.cameras != []:
			dists = {}

			for camera in self.level.cameras:
				x2 = self.range2range(camera.position.x(), 0, 500, 0, self.currentpmap.width())
				y2= self.range2range(camera.position.y(), 0,500, 0, self.currentpmap.height())

				dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

				dists[camera.id] = dist


			closestID = min(dists, key=dists.get)
			closestDist = dists.get(closestID)

			if closestDist < 10:
				return closestID
			else:
				return None
		else:
			return None

	def range2range(self, value, oldMin, oldMax, newMin, newMax):
		return ((value-oldMin)/(oldMax-oldMin)) * (newMax-newMin) + newMin

class LayoutControls(QFrame):
	def __init__(self, app, data, modes, painter, config):
		QFrame.__init__(self)
		self.setFrameStyle(QFrame.Box)
		self.config = config
		self.data = data
		self.painter = painter
		outerLayout = QVBoxLayout()
		self.setMaximumSize(QSize(1200, 100))
		self.setMinimumSize(QSize(700, 50))

		if LayoutMode.VIEW in modes:
			self.upLevelButton = QPushButton("Up")
			self.downLevelButton = QPushButton("Down")

			self.upLevelButton.clicked.connect(self.changeLevel)
			self.downLevelButton.clicked.connect(self.changeLevel)

			self.dropdown = QComboBox()
			self.dropdown.currentIndexChanged.connect(self.indexChanged)

			for i in range(len(data)):
				self.dropdown.addItem("Level " + str(data[i].id))#??

			viewLayout = QHBoxLayout()
			viewControlBox = QWidget()
			viewLayout.addWidget(self.upLevelButton)
			viewLayout.addWidget(self.downLevelButton)
			viewLayout.addWidget(self.dropdown)

			viewControlBox.setLayout(viewLayout)
			outerLayout.addWidget(viewControlBox, Qt.AlignCenter)

		if LayoutMode.EDIT in modes:
			addLevelButton = QPushButton("Add Level")
			addLevelButton.clicked.connect(self.addLevel)

			colorButton = QPushButton("Color")
			colorButton.clicked.connect(self.getColor)

			sizeButton = QPushButton("Size")
			sizeButton.clicked.connect(self.setSize)

			saveButton = QPushButton("Save")
			saveButton.clicked.connect(self.saveConfig)

			resetButton = QPushButton("Reset")
			resetButton.clicked.connect(self.resetConfig)


			editLayout = QHBoxLayout()
			editLayout.addWidget(addLevelButton)
			editLayout.addWidget(colorButton)
			editLayout.addWidget(sizeButton)
			editLayout.addWidget(saveButton)
			editLayout.addWidget(resetButton)

			outerLayout.addLayout(editLayout)

		self.setLayout(outerLayout)

	def changeLevel(self):
		if self.data != []:
			currentLevel = int(self.dropdown.currentText()[len("Level "):])

			if self.sender() is self.upLevelButton:
				nextLevel = currentLevel + 1
			elif self.sender() is self.downLevelButton:
				nextLevel = currentLevel - 1
			else:
				print("Unknown Caller: LayoutControls.changeLevel()")

			text = "Level " + str(nextLevel)
			index = self.dropdown.findText(text)

			if index != -1:
				self.dropdown.setCurrentIndex(index)#triggers indexChanged

	def indexChanged(self):
		level = int(self.dropdown.currentText()[len("Level "):])
		self.painter.currentLevel = level
		self.painter.repaint()

	def setLevel(self, level):
		text = "Level " + str(level)
		index = self.dropdown.findText(text)

		if index != -1:
			self.dropdown.setCurrentIndex(index)#triggers indexChanged

	def setMainFeedID(self, camera):
		self.painter.mainFeedID = camera.id
		self.setLevel(camera.levelID)
		self.painter.repaint()

	def addLevel(self):
		dialog = QInputDialog()
		id, check = dialog.getInt(self, "Level Setup", "Level Number")

		if check:
			dialog = QFileDialog()
			path, check = dialog.getOpenFileName()

			if check:
				level = Level(id, path, [])
				self.data.append(level)
				self.painter.levelIDs.append(id)
				self.dropdown.addItem("Level " + str(id))
				self.painter.repaint()
				self.config.levelMenu.update(self.data)

	def getColor(self):
		if self.data != []:
			prompt = QColorDialog()
			result = prompt.getColor()

			if result.isValid():
				self.setColor(result.getRgb()[:3])
		else:
			msgBox = QMessageBox()
			msgBox.setText("You must select a placed camera before you can edit its color")
			msgBox.exec()

	def setColor(self, color):
		newColor = QColor(color[0], color[1], color[2])
		camera = self.getSelectedCamera()
		camera.color = newColor
		self.painter.repaint()

	def saveConfig(self):
		if self.data != []:
			dataLoader = DataLoader()
			dataLoader.saveConfigData(self.data)

			msgBox = QMessageBox()
			msgBox.setText("Configuration data saved successfully.")
			msgBox.exec()
		else:
			msgBox = QMessageBox()
			msgBox.setText("Nothing to save.")
			msgBox.exec()


	def setSize(self):
		if self.data != []:
			dialog = QInputDialog()
			camera = self.getSelectedCamera()
			result = dialog.getInt(self, "Set Camera Size", "Label", camera.size, 5, 30, 1)
			if result[1]:
				camera.size = result[0]
				self.painter.repaint()
		else:
			msgBox = QMessageBox()
			msgBox.setText("You must select a placed camera before you can edit its size")
			msgBox.exec()

	def getSelectedCamera(self):
		for level in self.data:
			for camera in level.cameras:
				if camera.id == self.painter.mainFeedID:
					return camera

	def resetConfig(self):
		dialog = QMessageBox()
		dialog.setText("Are you sure?")
		dialog.setInformativeText("The configuration data will be permanently deleted.")
		dialog.setStandardButtons(QMessageBox.Reset | QMessageBox.Cancel)
		dialog.setDefaultButton(QMessageBox.Reset)
		result = dialog.exec()

		if result == QMessageBox.Reset:
			dataLoader = DataLoader()
			dataLoader.saveConfigData([])
			self.painter.data = []
			self.config.levelMenu.update(self.painter.data)
			msgBox = QMessageBox()
			msgBox.setText("Configuration data reset successfully.")
			msgBox.exec()
