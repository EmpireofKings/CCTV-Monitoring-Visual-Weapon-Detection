import json
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import os
from pprint import pprint

class Handler():
	def __init__(self):
		self.path = "../data/config.json"
		self.configData = self.parseData()

	def parseData(self):
		if not os.path.isfile(self.path):
			print("Configuration file missing")
			return None

		with open(self.path, 'r') as fp:
			levelData = json.load(fp)["levelData"]

		#represent json data as objects
		levels = []
		for level in levelData:
			levelID = level["levelID"]
			levelDrawPath = level["levelDrawPath"]
			levelCameras = []

			for cam in level["levelCameras"]:
				camID = cam.get("cameraID")
				camLocation = cam.get("cameraLocation")
				camPosition = cam.get("cameraCoordinates")
				camAngle = cam.get("cameraAngle")

				camera = Camera(camID, camLocation, camPosition, camAngle)
				levelCameras.append(camera)

			level = Level(levelID, levelDrawPath, levelCameras)
			levels.append(level)

		return levels

	def getConfigData(self):
		return self.configData

class Level():
	def __init__(self, id, drawPath, cameras):
		self.id = id
		self.drawPath = drawPath
		self.cameras = cameras

	def getCameraIDs(self):
		ids = []

		for camera in cameras:
			ids.append(camera.id)

		return ids

class Camera():
	def __init__(self, id, location, position, angle):
		self.id = id
		self.location = location
		self.position = position
		self.angle = angle
