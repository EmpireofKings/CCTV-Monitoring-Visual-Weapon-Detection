import cv2
import numpy as np
import easygui

filename = easygui.fileopenbox()
img = cv2.imread(filename)
shape = np.shape(img)
img = cv2.resize(img, (int(shape[1] * 2), int(shape[0] * 2)))
# imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

par = cv2.SimpleBlobDetector_Params()


blobDetector = cv2.SimpleBlobDetector_create(par)
blobs = blobDetector.detect(img)

for blob in blobs:
	img = cv2.drawMarker(
		img, tuple(int(i) for i in blob.pt),
		color=(0, 0, 255), thickness=2)


cv2.imshow('final', img)
cv2.waitKey(0)