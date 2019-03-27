import cv2
import numpy as np
import easygui

filename = easygui.fileopenbox()
img = cv2.imread(filename)
shape = np.shape(img)
img = cv2.resize(img, (shape[1] * 2, shape[0] * 2))
imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

harris = cv2.cornerHarris(imgGray, 2, 7, 0.05)
harris = cv2.dilate(harris, None)
img[harris > 0.01 * harris.max()] = [0, 0, 255]

cv2.imshow('final', img)
cv2.waitKey(0)