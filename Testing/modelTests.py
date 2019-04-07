import easygui
import cv2
import tensorflow as tf
from feed_process_helper import FeedProcessHelper
from results_handler import ResultsHandler
from terminator import Terminator
import numpy as np
import sys
import uuid
import time


def run():
	modelFile = easygui.fileopenbox('Choose a model')
	model = tf.keras.models.load_model(modelFile)
	model.summary()

	fph = FeedProcessHelper()
	resultsHandler = ResultsHandler(16, 5)

	options = ['Video', 'Camera', 'Image']
	choice = options[easygui.indexbox(msg='What do you want to use?', choices=options)]

	if choice == 'Video':
		videoFile = easygui.fileopenbox('Choose a video')
		feed = cv2.VideoCapture(videoFile)
	elif choice == 'Camera':
		feed = cv2.VideoCapture(0)
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		uniqueID = str(uuid.uuid4().hex)
		outStream = cv2.VideoWriter('../Samples/sampleVideo' + uniqueID + '.mp4', fourcc, fps=24.0, frameSize=(640, 480))

	elif choice == 'Image':
		imageFile = easygui.fileopenbox('Choose an image')
		image = cv2.imread(imageFile)

		regions, drawCoords = fph.extractRegions(image, 4, (64, 64))
		results = np.around(model.predict(regions)[:,10:], decimals=3)
		image = fph.drawResults(image, results, drawCoords, ["Weapon", "Weapon"])

		cv2.imshow("image", image)
		cv2.waitKey(0)
		sys.exit()

	FPS = feed.get(cv2.CAP_PROP_FPS)
	terminator = Terminator.getInstance()
	fpsTimer = time.time()
	while feed.isOpened() and not terminator.isTerminating():
		while time.time() - fpsTimer < 1 / FPS :
			time.sleep(0.001)

		fpsTimer = time.time()

		check, frame = feed.read()

		if check:
			if choice == 'Camera':
				outStream.write(frame)
			regions, drawCoords = fph.extractRegions(frame, 4, (64, 64))

			results = np.around(model.predict(regions)[:,10:], decimals=3)
			resultsHandler.append(results)
			frame = fph.drawResults(frame, resultsHandler.getAverages(), drawCoords, ["Weapon", "Weapon"])
			cv2.imshow("feed", frame)
			cv2.waitKey(1)
		else:
			feed.set(cv2.CAP_PROP_POS_FRAMES, 0)

	if choice == 'camera':
		outStream.release()
