import cv2
import numpy as np
import easygui


filename = easygui.fileopenbox()
img = cv2.imread(filename)
shape = np.shape(img)
img = cv2.resize(img, (shape[1] * 2, shape[0] * 2))
imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
imgGray = cv2.GaussianBlur(imgGray, (7,5), 0)

filter = cv2.ximgproc.RidgeDetectionFilter_create()
ridge = filter.getRidgeFilteredImage(imgGray)

img[ridge > 0.9 * ridge.max()] = [0, 0, 255]

cv2.imshow('final', img)
cv2.waitKey(0)
