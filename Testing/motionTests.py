from feed_process_helper import BackgroundRemover
import cv2
import numpy as np

def run():
	bgRemover = BackgroundRemover()

	feed = cv2.VideoCapture(0)

	while feed.isOpened():
		check, frame = feed.read()

		if check:
			bbox = bgRemover.apply(frame)

			if bbox != []:
				height, width, _ = np.shape(frame)
				for box in bbox:
					x, y, w, h = box
					x = int(bgRemover.scale(x, 0, 1, 0, width))
					y = int(bgRemover.scale(y, 0, 1, 0, height))
					w = int(bgRemover.scale(w, 0, 1, 0, width))
					h = int(bgRemover.scale(h, 0, 1, 0, height))

					cv2.rectangle(
						frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
			
			cv2.imshow('feed', frame)
			cv2.waitKey(1)