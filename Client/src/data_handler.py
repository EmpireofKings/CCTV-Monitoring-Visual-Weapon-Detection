import json
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import os
from pprint import pprint
import copy
import cv2
import numpy as np

class DataLoader():
	def __init__(self):
		self.path = "../data/config.json"
		self.configData = self.parseData()

	def parseData(self):
		if not os.path.isfile(self.path):
			print("Configuration file missing")
			return None

		with open(self.path, 'r') as fp:
			levelData = json.load(fp)

		#represent json data as objects
		levels = []
		levelIDs = []
		for level in levelData:
			levelID = level["levelID"]
			levelDrawPath = level["levelDrawPath"]
			levelCameras = []

			for cam in level["levelCameras"]:
				camID = cam.get("cameraID")
				camLocation = cam.get("cameraLocation")

				x = cam.get("cameraCoordinates")[0]
				y = cam.get("cameraCoordinates")[1]
				camPosition = QPoint(x, y)

				camAngle = cam.get("cameraAngle")

				r = cam.get("cameraColor")[0]
				g = cam.get("cameraColor")[1]
				b = cam.get("cameraColor")[2]
				camColor = QColor(r, g, b)
				camSize = cam.get("cameraSize")

				camera = Camera(camID, levelID, camLocation, camPosition, camAngle, camColor, camSize)
				levelCameras.append(camera)

			level = Level(levelID, levelDrawPath, levelCameras)
			levels.append(level)
			levelIDs.append(levelID)


		return levels, levelIDs

	def getConfigData(self):
		return self.configData

	def saveConfigData(self, configData):
		data = []

		for level in configData:
			pprint(level)
			data.append(level.getSaveableForm())

		with open('../data/config.json', 'w') as fp:
			json.dump(data, fp)

#Encapuslators:

class Level():
	def __init__(self, id, drawPath, cameras):
		self.id = id
		self.drawPath = drawPath
		self.cameras = cameras
		self.pmap = None

	def getCameraIDs(self):
		ids = []

		for camera in self.cameras:
			ids.append(camera.id)

		return ids

	def getSaveableForm(self):
		level = {}
		level["levelID"] = self.id
		level["levelDrawPath"] = self.drawPath
		cams = []

		for camera in self.cameras:
			cams.append(camera.getSaveableForm())

		level["levelCameras"] = cams
		return level

class Camera():
	def __init__(self, id, levelID, location, position, angle, color, size):
		self.id = id
		self.levelID = levelID
		self.location = location
		self.position = position
		self.angle = angle
		self.color = color
		self.size = size

	def getPreview(self, width, height):
		if self.id.isdigit():
			feed = cv2.VideoCapture(int(self.id))
		else:
			feed = cv2.VideoCapture(self.id)

		if feed.isOpened():
			check, frame = feed.read()

			if check:
				feed.release()
				return getLabelledPixmap(width, height, self.id , path = None, pmap = nd2pmap(frame))
			else:
				print("Error acquiring feed preview.")

	def getSaveableForm(self):
		cam = {}
		cam["cameraID"] = self.id
		cam["cameraLocation"] = self.location
		cam["cameraCoordinates"] = [self.position.x(), self.position.y()]
		cam["cameraAngle"] = self.angle
		r, g, b, _ = self.color.getRgb()
		cam["cameraColor"] = [r, g, b]
		cam["cameraSize"] = self.size

		return cam

def nd2pmap(frame):
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	h, w, c = np.shape(frame)
	pmap = QPixmap.fromImage(QImage(frame.data, w, h, w*c,  QImage.Format_RGB888))
	return pmap

def getPixmap(width, height, path):
	return QPixmap(path).scaled(QSize(width, height))

def getLabelledPixmap(width, height, label, path, pmap = None):
	if pmap is None:
		pmap = getPixmap(width, height, path)
	else:
		pmap = pmap.scaled(width, height)

	painter = QPainter(pmap)

	cx = width/2
	cy = height/2
	grad = QRadialGradient(cx, cy, width, cx, cx)
	painter.setBrush(QBrush(grad))

	painter.setOpacity(0.6)
	painter.drawRect(QRect(0,0,width, height))

	painter.setOpacity(1.0)
	painter.setPen(QPen(QColor(255,255,255)))

	fontSize = 30
	font = QFont("Helvetica [Cronyx]", fontSize)
	met = QFontMetrics(font)

	while met.width(label) >= width:
		fontSize -= 1
		font = QFont("Helvetica [Cronyx]", fontSize)
		met = QFontMetrics(font)

	painter.setFont(font)

	painter.drawText(QRect(0, 0, width, height), Qt.AlignCenter, label)

	return pmap
