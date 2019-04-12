# Ben Ryan C15507277

import cv2
import easygui
import numpy as np


def run():
	filename = easygui.fileopenbox('Choose an image')
	img = cv2.imread(filename)

	imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	imgGray = cv2.GaussianBlur(imgGray, (7, 5), 0)

	filter = cv2.ximgproc.RidgeDetectionFilter_create()
	ridge = filter.getRidgeFilteredImage(imgGray)

	img[ridge > 0.9 * ridge.max()] = [0, 0, 255]

	cv2.imshow('Detected ridges in red', img)
	cv2.waitKey(0)
