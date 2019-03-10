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
	def __init__(self, feed):
		self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(5, 5))

		while feed.isOpened():
			check, frame = feed.read()

			if check:
				cv2.imshow("Press enter to capture background", frame)
				key = cv2.waitKey(0)

			if key == 13:
				gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
				blurred = cv2.GaussianBlur(gray, (5, 5), 0)
				self.background = self.clahe.apply(blurred)
				break

	def drawBoundingBox(self, frame):
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		blurred = cv2.GaussianBlur(gray, (5, 5), 0)
		equalized = self.clahe.apply(blurred)

		diff = cv2.absdiff(equalized, self.background)
		_, binary = cv2.threshold(diff, 60, 255, cv2.THRESH_BINARY)
		structEl = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

		opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, structEl)

		_, contours, _ = cv2.findContours(
			opened, cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)

		if len(contours) > 0:
			largest = max(contours, key=cv2.contourArea)

			x, y, w, h = cv2.boundingRect(largest)
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

		return frame

