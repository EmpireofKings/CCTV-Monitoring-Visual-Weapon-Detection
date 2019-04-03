import tensorflow as tf
import cv2
import numpy as np
import sys
import easygui
from tensorflow.keras.applications.nasnet import NASNetLarge, preprocess_input, decode_predictions
from keras.utils import plot_model
from collections import deque
from pprint import pprint
import time
from feed_process_helper import BackgroundRemover

from matplotlib import pyplot as plt

def pretrained():
	model = NASNetLarge(weights='imagenet')
	#model.summary()

	feed = getVideoFeed()

	while feed.isOpened():
		check, frame = feed.read()

		if check:
			regions, drawCoords = extractRegions(frame, 3, (331,331), False)
			print(np.shape(regions))

			regions = preprocess_input(regions)
			results = model.predict(regions)

			print("Predicted", decode_predictions(results, top=3))

			for count in range(len(results)-1):
				top3 = decode_predictions(results, top=3)[count]

				regionX, regionY, regionW, regionH = drawCoords[count]

				cv2.rectangle(frame, (regionX, regionY), (regionX+regionW, regionY+regionH), (255,0,0), 3)
				cv2.putText(frame, str(top3[2][1]), (regionX+10, regionY+regionH-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)
				cv2.putText(frame, str(top3[1][1]), (regionX+10, regionY+regionH-30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)
				cv2.putText(frame, str(top3[0][1]), (regionX+10, regionY+regionH-50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)

			cv2.imshow(str(decode_predictions(results, top=3)[len(results)-1]), frame)
			cv2.waitKey(1)
			# cv2.destroyAllWindows()

def getVideoFeed():
	videoFile = easygui.fileopenbox()
	feed = cv2.VideoCapture(videoFile)
	return feed

def getCameraFeed():
	return cv2.VideoCapture(0)

def extractRegions(frame, gridSize, regionSize, prepare = True, offset = False, offsetX = 0, offsetY = 0):
	h, w, c = np.shape(frame)

	regionH = int(h/gridSize)
	regionW = int(w/gridSize)

	regions = []
	drawCoords = []
	for row in range(gridSize):
		regionY = row * regionH
		for col in range(gridSize):
			regionX = col * regionW

			region = frame[regionY: regionY+regionH, regionX:regionX+regionW]
			#cv2.imshow("region", region)
			
			if offset:
				drawCoords.append((regionX+offsetX, regionY+offsetY, regionW, regionH))
			else:
				drawCoords.append((regionX, regionY, regionW, regionH))


			region = cv2.resize(region, regionSize)
			region = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)

			if prepare is True:
				region = region / 255.0

			regions.append(region)

	# if offset is False:
	# 	subX = int(regionW/2)
	# 	subWidth = w-subX
	# 	subY = int(regionH/2)
	# 	subHeight = h-subY
	# 	subImage = frame[subY:subHeight, subX:subWidth]
	# 	extraRegions, extraDraw = extractRegions(subImage, 2, (64,64), offset=True, offsetX=subX, offsetY=subY)
		
	# 	for count in range(len(extraRegions)):
	# 		regions.append(extraRegions[count])python
	# 		drawCoords.append(extraDraw[count])

	return np.array(regions), drawCoords

def interpretResults():
	#model = getDefaultModel()
	model = chooseModel()
	model.summary()
	#plot_model(model, to_file='./modelGraph.png')
	feed = getCameraFeed()
	# feed = getVideoFeed()
	resultHandler1 = ResultsHandler(4, 1)
	resultHandler2 = ResultsHandler(9, 1)
	resultHandler3 = ResultsHandler(16, 1)
	resultHandler4 = ResultsHandler(25, 1)
	resultHandler5 = ResultsHandler(36, 1)
	resultHandler6 = ResultsHandler(49, 1)
	resultHandler7 = ResultsHandler(64, 1)

	bgRemover = BackgroundRemover()
	alertTimer = None

	
	while feed.isOpened():
		check, frame = feed.read()

		if check:
			# region = frame.copy()
			# region = cv2.resize(region, (331, 331))
			# region = np.expand_dims(region, axis=0)
			# results = np.around(model.predict(region)[:,10:], decimals=3)
			# frame = drawResults(frame, results, [(0,0,331,331)], ["Knife", "Pistol"], all=True)

			boundingBoxes = bgRemover.apply(frame)
			regions = []
			drawCoords = []

			regions1, drawCoords1 = extractRegions(frame, 2, (64, 64), True)
			regions2, drawCoords2 = extractRegions(frame, 3, (64, 64), True)
			regions3, drawCoords3 = extractRegions(frame, 4, (64, 64), True)
			regions4, drawCoords4 = extractRegions(frame, 5, (64, 64), True)
			regions5, drawCoords5 = extractRegions(frame, 6, (64, 64), True)
			regions6, drawCoords6 = extractRegions(frame, 7, (64, 64), True)
			regions7, drawCoords7 = extractRegions(frame, 8, (64, 64), True)

			results1 = np.around(model.predict(regions1)[:,10:], decimals=3)
			results2 = np.around(model.predict(regions2)[:,10:], decimals=3)
			results3 = np.around(model.predict(regions3)[:,10:], decimals=3)
			results4 = np.around(model.predict(regions4)[:,10:], decimals=3)
			results5 = np.around(model.predict(regions5)[:,10:], decimals=3)
			results6 = np.around(model.predict(regions6)[:,10:], decimals=3)
			results7 = np.around(model.predict(regions7)[:,10:], decimals=3)


			resultHandler1.append(results1)
			resultHandler2.append(results2)
			resultHandler3.append(results3)
			resultHandler4.append(results4)
			resultHandler5.append(results5)
			resultHandler6.append(results6)
			resultHandler7.append(results7)

			#alert = resultHandler.assess()

			#print(alert)

			# if alert or alertTimer is not None:
			# 	if alert is True or alertTimer is None:
			# 		alertTimer = time.time()
				
			# 	print(time.time() - alertTimer)
			# 	# frame = bgRemover.drawBoundingBox(frame)

			# 	if time.time() - alertTimer >= 5:
			# 		print("reset")
			# 		alertTimer = None
			


			frame = drawResults(frame, resultHandler1.getAverages(), drawCoords1, ["Weapon", "Weapon"])
			frame = drawResults(frame, resultHandler2.getAverages(), drawCoords2, ["Weapon", "Weapon"])
			frame = drawResults(frame, resultHandler3.getAverages(), drawCoords3, ["Weapon", "Weapon"])
			frame = drawResults(frame, resultHandler4.getAverages(), drawCoords4, ["Weapon", "Weapon"])
			frame = drawResults(frame, resultHandler5.getAverages(), drawCoords5, ["Weapon", "Weapon"])
			frame = drawResults(frame, resultHandler6.getAverages(), drawCoords6, ["Weapon", "Weapon"])
			frame = drawResults(frame, resultHandler7.getAverages(), drawCoords7, ["Weapon", "Weapon"])

			if boundingBoxes != []:
				height, width, _ = np.shape(frame)
				for box in boundingBoxes:
					x, y, w, h = box
					x = int(scale(x, 0, 1, 0, width))
					y = int(scale(y, 0, 1, 0, height))
					w = int(scale(w, 0, 1, 0, width))
					h = int(scale(h, 0, 1, 0, height))

					# drawCoords.append((x, y, w, h))
					# region = frame[y:y + h, x:x + w]
					# region = cv2.resize(region, (64, 64))
					# regions.append(region)

				# regions = np.array(regions)
				# results = np.around(model.predict(regions)[:,10:], decimals=3)

				# drawResults(frame, results, drawCoords, ["Weapon", "Weapon"], all=True)

					cv2.rectangle(
						frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
			
			
			cv2.imshow("feed", frame)
			cv2.waitKey(1)
		else:
			feed.set(cv2.CAP_PROP_POS_FRAMES, 0)
	
def scale(val, inMin, inMax, outMin, outMax):
	return ((val - inMin) / (inMax - inMin)) * (outMax - outMin) + outMin


class ResultsHandler():
	def __init__(self, amount, size):
		
		self.buffers = []
		for _ in range(amount):
			buf = self.ResultBuffer(size)
			self.buffers.append(buf)

	def getAverages(self):
		averages = []
		for buf in self.buffers:
			avg = buf.getAvg()
			averages.append(avg)

		return averages

	def getLengths(self):
		lengths = []
		for buf in self.buffers:
			l = len(buf)
			lengths.append(l)

		return lengths

	def __len__(self):
		return len(self.buffers)

	def append(self, results):
		for count in range(len(self.buffers)):
			buffer = self.buffers[count]
			resultSet = results[count]

			buffer.append(resultSet[0], resultSet[1])

	def assess(self):
		averages = self.getAverages()

		for avg in averages:
			if max(avg) > 0.95:
				return True


	class ResultBuffer():
		def __init__(self, size):
			self.knifeBuffer = deque(maxlen=size)
			self.pistolBuffer = deque(maxlen=size)

		def getAvg(self):
			knifeAvg = sum(self.knifeBuffer)/len(self.knifeBuffer)
			pistolAvg = sum(self.pistolBuffer)/len(self.pistolBuffer)

			return (knifeAvg, pistolAvg)

		def __len__(self):
			length = len(self.knifeBuffer)
			if length == len(self.pistolBuffer):
				return length
			else:
				return -1

		def append(self, knife, pistol):
			self.knifeBuffer.append(knife)
			self.pistolBuffer.append(pistol)

			


def drawResults(img, results, drawCoords, categories, all=False):
	for count in range(len(results)):
		regionResults = results[count]
		highest = np.argmax(regionResults)

		if regionResults[highest] >= 0.95:
			label = categories[highest]
			regionX, regionY, regionW, regionH = drawCoords[count]
			cv2.rectangle(img, (regionX, regionY), (regionX+regionW, regionY+regionH), (0,0,255), 3)
			cv2.putText(img, label, (regionX+10, regionY+regionH-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
			cv2.putText(img, str(regionResults[highest]), (regionX+10, regionY+regionH-60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

		elif all:
			label = "Clear"
			regionX, regionY, regionW, regionH = drawCoords[count]
			cv2.rectangle(img, (regionX, regionY), (regionX+regionW, regionY+regionH), (0,255,0), 1)

	return img

	
def getDefaultModel():
	path = "../Decent Models/defaultModel.h5"

	model = tf.keras.models.load_model(path)
	model.summary()

	return model

def chooseModel():
	modelFile = easygui.fileopenbox()

	model = tf.keras.models.load_model(modelFile)
	#model.summary()

	return model

def displayAllResults():
	model = chooseModel()

	# feed = getVideoFeed()
	feed = getCameraFeed()

	categories = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck", "Knife", "Pistol"]

	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	outStream = cv2.VideoWriter('./testing.mp4', fourcc, frameSize=(640,480), fps=30.0)

	terminator = Terminator()

	while feed.isOpened():
		check, frame = feed.read()
		print(np.shape(frame))

		if check:
			dispFrame = frame.copy()

			outStream.write(frame)

			if terminator.isTerminating():
				outStream.release()
				sys.exit()

			fullscan = cv2.resize(frame, (64,64))
			fullscan = np.expand_dims(fullscan, axis=0)
			res = model.predict(fullscan)

			# highest = np.argmax(res[0])
			#
			# if res[0][highest] > 0.5:
			# 	cv2.imshow(categories[highest], dispFrame)
			# 	cv2.waitKey(0)


			regions, drawCoords = extractRegions(frame, 3, (64, 64), True)

			results = model.predict(regions)
			# print(str(results))

			results = np.around(results, decimals=3)
			# print(str(results))

			for count in range(len(results)):
				regionResults = results[count]
				highest = np.argmax(regionResults)

				if len(regionResults) == 2:
					categories = ["Knife", "Pistol"]

				color = (255,0,0)
				if regionResults[highest] > 0.9:
					label = categories[highest]

					if label == "Knife" or label == "Pistol":
						color = (0,0,255)
				else:
					label = "Clear"
					color = (0,255,0)

				regionX, regionY, regionW, regionH = drawCoords[count]
				cv2.rectangle(dispFrame, (regionX, regionY), (regionX+regionW, regionY+regionH), color, 3)
				cv2.putText(dispFrame, label, (regionX+10, regionY+regionH-10), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 2)


			cv2.imshow("frame", dispFrame)
			cv2.waitKey(1)
			#cv2.destroyAllWindows()




if __name__ == '__main__':
	interpretResults()
	#displayAllResults()
	#pretrained()
	
