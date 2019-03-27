import cv2
import numpy as np
import easygui

filename = easygui.fileopenbox()
img = cv2.imread(filename)
shape = np.shape(img)
img = cv2.resize(img, (shape[1] * 2, shape[0] * 2))
imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

sobelX = cv2.Sobel(imgGray, cv2.CV_64F, 1, 0, 3)
sobelY = cv2.Sobel(imgGray, cv2.CV_64F, 0, 1, 3)


img[sobelX > 0.1 * sobelX.max()] = [0, 0, 255]
# img[sobelY > 0.25 * sobelY.max()] = [0, 0, 255]

cv2.imshow("sobX", sobelX.astype(np.uint8))
cv2.imshow("sobY", sobelY.astype(np.uint8))
cv2.imshow('final', img)


cv2.waitKey(0)
