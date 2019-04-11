import unittest
import os
import sys

path = os.getcwd().split('\\')
path = '\\'.join(path[:len(path)])
sys.path.append(path + '\\CommonFiles')
sys.path.append(path + '\\Client\\src')
sys.path.append(path + '\\Server\\src')

from feed_process_helper import FeedProcessHelper
from results_handler import ResultsHandler
from data_handler import Camera, Level
import numpy as np
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class RegionExtraction(unittest.TestCase):
	def setUp(self):
		self.fph = FeedProcessHelper()

		randomData = np.random.rand(50, 50, 3).astype(np.uint8)

		self.regions, self.drawCoords = self.fph.extractRegions(randomData, 3, (64, 64))

	def testMatchingAmount(self):
		self.assertEqual(len(self.regions), len(self.drawCoords))

	def testExtractedAmount(self):
		self.assertEqual(len(self.regions), 9)

	def testRegionShape(self):
		for region in self.regions:
			shape = np.shape(region)
			self.assertEqual(shape, (64, 64, 3))


class ResultsHandling(unittest.TestCase):
	def setUp(self):
		self.handler = ResultsHandler(9, 5)
		self.randomData = np.random.rand(9,2)

		for _ in range(10):
			self.handler.append(self.randomData)

	def testBuffersLengths(self):
		self.assertEqual(self.handler.getLengths()[0], self.handler.getLengths()[1])

	def testMaxLength(self):
		self.assertTrue(self.handler.getLengths()[0] <= 5)


class CameraEncapsulation(unittest.TestCase):
	def setUp(self):
		self.cam = Camera(
			camID='sampleID', levelID='sampleID', location='sampleLocation',
			position=QPoint(10, 10), angle=150, color=QColor(50, 50, 50), size=10, assigned=False)

		self.data = self.cam.getSaveableForm()

	def getCam(self):
		return self.cam

	def testID(self):
		camID = self.data.get("cameraID")
		self.assertEqual(camID, 'sampleID')

	def testLocation(self):
		cameraLocation = self.data.get("cameraLocation")
		self.assertEqual(cameraLocation, 'sampleLocation')

	def testCoordinates(self):
		coords = self.data.get("cameraCoordinates")
		self.assertEqual(coords, [10, 10])

	def testAngle(self):
		angle = self.data.get("cameraAngle")
		self.assertEqual(angle, 150)

	def testColor(self):
		color = self.data.get("cameraColor")
		self.assertEqual(color, [50, 50, 50])

	def testSize(self):
		size = self.data.get("cameraSize")
		self.assertEqual(size, 10)


class LevelEncapsulation(unittest.TestCase):
	def setUp(self):
		# reuse
		camEncap = CameraEncapsulation()
		camEncap.setUp()
		self.camera = camEncap.getCam()

		level = Level(levelID='sampleID', drawPath='samplePath', cameras=[self.camera])

		self.data = level.getSaveableForm()

	def testID(self):
		levelID = self.data.get("levelID")
		self.assertEqual(levelID, 'sampleID')

	def testPath(self):
		path = self.data.get("levelDrawPath")
		self.assertEqual(path, 'samplePath')

	def testCam(self):
		cam = self.data.get("levelCameras")[0]
		expected = self.camera.getSaveableForm()
		self.assertEqual(expected, cam)


def runAutomated():
	unittest.main()

if __name__ == '__main__':
	unittest.main()
