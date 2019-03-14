import copy
import json
import os
from pprint import pprint

import cv2
import numpy as np
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


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

		# represent json data as objects
		levels = []
		levelIDs = []
		cameraIDs = []
		for level in levelData:
			levelID = level["levelID"]
			levelDrawPath = level["levelDrawPath"]
			levelCameras = []

			for cam in level["levelCameras"]:
				camID = cam.get("cameraID")
				cameraIDs.append(camID)
				camName = cam.get("cameraName")
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

				camera = Camera(camID, camName, levelID, camLocation, camPosition, camAngle, camColor, camSize, assigned = True)
				levelCameras.append(camera)

			level = Level(levelID, levelDrawPath, levelCameras)
			levels.append(level)
			levelIDs.append(levelID)

		# CAP_DSHOW and CAP_MSMF removed as they were producing duplicate cameras
		apis = {
			"CAP_ANY": 0,
			# "CAP_VFW": 200,
			# "CAP_V4L": 200,
			"CAP_FIREWIRE": 300,
			"CAP_QT": 500,
			"CAP_UNICAP": 600,
			# "CAP_DSHOW" : 700,
			"CAP_PVAPI": 800,
			"CAP_OPENNI": 900,
			"CAP_OPENNI_ASUS": 910,
			"CAP_ANDROID": 1000,
			"CAP_XIAPI": 1100,
			"CAP_AVFOUNDATION": 1200,
			"CAP_GIGANETIX": 1300,
			# "CAP_MSMF": 1400,
			"CAP_WINRT": 1410,
			"CAP_INTELPERC": 1500,
			"CAP_OPENNI2": 1600,
			"CAP_OPENNI2_ASUS": 1610,
			"CAP_GPHOTO2": 1700,
			"CAP_GSTREAMER": 1800,
			"CAP_FFMPEG": 1900,
			"CAP_IMAGES": 2000,
			"CAP_ARAVIS": 2100,
			"CAP_OPENCV_MJPEG": 2200,
			"CAP_INTEL_MFX": 2300}

		unassignedCameras = []

		for api in apis.items():
			api = api[1]

			for id in range(10):
				if str(id) not in cameraIDs:
					try:
						feed = cv2.VideoCapture(id + api)

						if feed.isOpened():
							feed.release()
							camera = Camera(str(id + api), str(id + api))
							unassignedCameras.append(camera)
					except Exception as e:
						print(e)

		return [levels, unassignedCameras]

	def getConfigData(self):
		return self.configData

	def saveConfigData(self, configData):
		data = []

		for level in configData:
			data.append(level.getSaveableForm())

		with open('../data/config.json', 'w') as fp:
			json.dump(data, fp, indent=4)

# Encapuslators:


class Level():
	def __init__(self, levelID, drawPath, cameras):
		self.levelID = levelID
		self.drawPath = os.path.relpath(drawPath)
		self.cameras = cameras
		self.pmap = None

	def getCameraIDs(self):
		ids = []

		for camera in self.cameras:
			ids.append(camera.id)

		return ids

	def getSaveableForm(self):
		level = {}
		level["levelID"] = self.levelID
		level["levelDrawPath"] = self.drawPath
		cams = []

		for camera in self.cameras:
			cams.append(camera.getSaveableForm())

		level["levelCameras"] = cams
		return level


class Camera():
	def __init__(
		self, camID, name, levelID=None, location=None, position=None,
		angle=None, color=None, size=None, staticBackground=None, assigned=False):

		if camID.isdigit():
			self.camID = camID
		else:
			self.camID = os.path.relpath(camID)

		self.name = name
		self.levelID = levelID
		self.location = location
		self.position = position
		self.angle = angle
		self.color = color
		self.size = size
		self.staticBackground = staticBackground
		self.assigned = assigned
		self.preview = None

	def getPreview(self, width, height):
		if self.preview is None:
			if self.camID.isdigit():
				feed = cv2.VideoCapture(int(self.camID))
			else:
				feed = cv2.VideoCapture(self.camID)

			if feed.isOpened():
				check, frame = feed.read()

				if check:
					feed.release()
					del feed
					self.preview = getLabelledPixmap(width, height, self.name, path = None, pmap = nd2pmap(frame))
			else:
				print("Error acquiring feed preview. (ID:", self.camID, ")" )

		return self.preview


	def getSaveableForm(self):
		cam = {}
		cam["cameraID"] = str(self.camID)
		cam["cameraName"] = str(self.name)
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

def getLabelledPixmap(width, height, label, path=None, pmap=None):
	if pmap is None:
		pmap = getPixmap(width, height, path)
	else:
		pmap = pmap.scaled(width, height)

	painter = QPainter(pmap)

	cx = width / 2
	cy = height / 2
	grad = QRadialGradient(cx, cy, width, cx, cx)
	painter.setBrush(QBrush(grad))

	painter.setOpacity(0.6)
	painter.drawRect(QRect(0, 0, width, height))

	painter.setOpacity(1.0)
	painter.setPen(QPen(QColor(255, 255, 255)))

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
