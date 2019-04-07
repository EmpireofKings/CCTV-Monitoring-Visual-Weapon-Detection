import easygui
import cv2
import tensorflow as tf
from feed_process_helper import FeedProcessHelper
from results_handler import ResultsHandler
import numpy as np
import sys


def run():
	modelFile = easygui.fileopenbox('Choose a model')
	model = tf.keras.models.load_model(modelFile)
	model.summary()

	fph = FeedProcessHelper()
	resultsHandler = ResultsHandler(9, 5)

	options = ['Video', 'Camera', 'Image']
	choice = options[easygui.indexbox(msg='What do you want to use?', choices=options)]

	if choice == 'Video':
		videoFile = easygui.fileopenbox('Choose a video')
		feed = cv2.VideoCapture(videoFile)
	elif choice == 'Camera':
		feed = cv2.VideoCapture(0)
	elif choice == 'Image':
		imageFile = easygui.fileopenbox('Choose an image')
		image = cv2.imread(imageFile)

		regions, drawCoords = fph.extractRegions(image, 3, (64, 64))
		results = np.around(model.predict(regions)[:,10:], decimals=3)
		image = fph.drawResults(image, results, drawCoords, ["Knife", "Pistol"])

		cv2.imshow("image", image)
		cv2.waitKey(0)
		sys.exit()

	while feed.isOpened():
		check, frame = feed.read()

		if check:
			regions, drawCoords = fph.extractRegions(frame, 3, (64, 64))

			results = np.around(model.predict(regions)[:,10:], decimals=3)
			resultsHandler.append(results)
			frame = fph.drawResults(frame, resultsHandler.getAverages(), drawCoords, ["Knife", "Pistol"])
			cv2.imshow("feed", frame)
			cv2.waitKey(1)
		else:
			feed.set(cv2.CAP_PROP_POS_FRAMES, 0)
