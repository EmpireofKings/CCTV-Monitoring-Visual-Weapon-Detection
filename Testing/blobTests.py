import cv2
import numpy as np
import easygui


def run():
	filename = easygui.fileopenbox('Choose an image')
	img = cv2.imread(filename)

	par = cv2.SimpleBlobDetector_Params()

	blobDetector = cv2.SimpleBlobDetector_create(par)
	blobs = blobDetector.detect(img)

	for blob in blobs:
		img = cv2.drawMarker(
			img, tuple(int(i) for i in blob.pt),
			color=(0, 0, 255), thickness=2)

	cv2.imshow('Detected blobs in red', img)
	cv2.waitKey(0)
