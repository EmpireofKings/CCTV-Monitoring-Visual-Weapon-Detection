import cv2
import numpy as np


class FeedProcessHelper():
	def extractRegions(
		self, frame, gridSize, regionSize, prepare=True, offset=False,
		offsetX=0, offsetY=0):

		h, w, c = np.shape(frame)

		regionH = int(h / gridSize)
		regionW = int(w / gridSize)

		regions = []
		drawCoords = []
		for row in range(gridSize):
			regionY = row * regionH
			for col in range(gridSize):
				regionX = col * regionW

				region = frame[regionY: regionY + regionH, regionX:regionX + regionW]

				if offset:
					drawCoords.append((
						regionX + offsetX, regionY + offsetY,
						regionW, regionH))
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
		# 	extraRegions, extraDraw = extractRegions(
		# 		subImage, 2, (64,64), offset = True,
		# 		offsetX = subX, offsetY = subY)

		# 	for count in range(len(extraRegions)):
		# 		regions.append(extraRegions[count])
		# 		drawCoords.append(extraDraw[count])

		return np.array(regions), drawCoords

	def drawResults(self, img, results, drawCoords, categories, all=False):
		for count in range(len(results)):
			regionResults = results[count]
			highest = np.argmax(regionResults)

			if regionResults[highest] > 0:
				label = categories[highest]
				regionX, regionY, regionW, regionH = drawCoords[count]
				cv2.rectangle(
					img, (regionX, regionY), (regionX + regionW, regionY + regionH),
					(0, 0, 255), 3)

				cv2.putText(
					img, label, (regionX + 10, regionY + regionH - 10),
					cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

				cv2.putText(
					img, str(regionResults[highest]),
					(regionX + 10, regionY + regionH - 60),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

			elif all:
				label = "Clear"
				regionX, regionY, regionW, regionH = drawCoords[count]
				cv2.rectangle(
					img, (regionX, regionY),
					(regionX + regionW, regionY + regionH), (0, 255, 0), 1)

		return img


class BackgroundRemover():
	def __init__(self):
		self.remover = cv2.createBackgroundSubtractorMOG2()

		self.openElement = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
		self.closeElement = cv2.getStructuringElement(cv2.MORPH_RECT, (30,30))

	def apply(self, frame):
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		frame = cv2.GaussianBlur(frame, (19, 19), 0)

		mask = self.remover.apply(frame)

		mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.openElement)
		mask = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, self.openElement)
		mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.closeElement)

		height, width = np.shape(frame)
		minArea = (height*width) * 0.0075

		contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		contours = sorted(contours, key=cv2.contourArea)

		boundingBoxes = []
		for contour in contours:
			if cv2.contourArea(contour) > minArea and len(boundingBoxes) < 5:
				xf, yf, wf, hf = cv2.boundingRect(contour)
				x = self.scale(xf, 0, width, 0, 1)
				y = self.scale(yf, 0, height, 0, 1)
				w = self.scale(wf, 0, width, 0, 1)
				h = self.scale(hf, 0, height, 0, 1)

				boundingBoxes.append([x, y, w, h])
			else:
				break

		return boundingBoxes

	def scale(self, val, inMin, inMax, outMin, outMax):
		return ((val - inMin) / (inMax - inMin)) * (outMax - outMin) + outMin
