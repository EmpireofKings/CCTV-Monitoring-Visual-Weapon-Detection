# Ben Ryan C15507277

import cv2
import easygui
import numpy as np


def run():
	filename = easygui.fileopenbox('Choose an image')
	img = cv2.imread(filename)

	imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	canny = cv2.Canny(imgGray, 150, 200)
	canny = cv2.dilate(canny, None)
	img[canny > 0.01 * canny.max()] = [0, 0, 255]

	cv2.imshow('Detected edges in red', img)
	cv2.waitKey(0)
