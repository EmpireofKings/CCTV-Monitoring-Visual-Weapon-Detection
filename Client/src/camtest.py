import cv2
import numpy as np

cameraid = "0"

camID = int(cameraid)
feed = cv2.VideoCapture(camID)

while feed.isOpened():
	check, frame = feed.read()

	if check:
		cv2.imshow('frame', frame)
		cv2.waitKey(1)
