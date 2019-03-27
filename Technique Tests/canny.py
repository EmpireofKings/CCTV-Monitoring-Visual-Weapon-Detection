import cv2
import numpy as np
import easygui

filename = easygui.fileopenbox()
img = cv2.imread(filename)
shape = np.shape(img)
img = cv2.resize(img, (shape[1] * 2, shape[0] * 2))
imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

canny = cv2.Canny(imgGray, 150, 200)
canny = cv2.dilate(canny, None)
img[canny > 0.01 * canny.max()] = [0, 0, 255]

cv2.imshow('final', img)
cv2.waitKey(0)
