import tensorflow as tf
import cv2
import numpy as np
import sys
import tensorflow as tf
import easygui

modelFile = easygui.fileopenbox()

model = tf.keras.models.load_model(modelFile)
model.summary()

videoFile = easygui.fileopenbox()

feed = cv2.VideoCapture(videoFile)

categories = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck", "Knife", "Pistol"]

while feed.isOpened():
	check, frame = feed.read()

	if check:
		dispFrame = frame.copy()
		h, w, c = np.shape(frame)

		fullscan = cv2.resize(frame, (64,64))
		fullscan = np.expand_dims(fullscan, axis=0)
		res = model.predict(fullscan)

		# highest = np.argmax(res[0])
		#
		# if res[0][highest] > 0.5:
		# 	cv2.imshow(categories[highest], dispFrame)
		# 	cv2.waitKey(0)

		gridSize = 4
		regionH = int(h/gridSize)
		regionW = int(w/gridSize)

		regions = []
		drawCoords = []
		for row in range(gridSize):
			regionY = row * regionH
			for col in range(gridSize):
				regionX = col * regionW

				region = frame[regionY: regionY+regionH, regionX:regionX+regionW]
				drawCoords.append((regionX, regionY, regionW, regionH))

				region = cv2.resize(region, (64, 64))
				region = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
				region = region / 255.0
				regions.append(region)

		regions.append(cv2.resize(frame.copy(),(64,64)))
		drawCoords.append((0, 0, w, h))
		regions = np.array(regions)

		results = model.predict(regions)
		print(str(results))

		results = np.around(results, decimals=3)
		print(str(results))

		for count in range(len(results)):
			regionResults = results[count]
			highest = np.argmax(regionResults)

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
		cv2.waitKey(0)
		cv2.destroyAllWindows()
