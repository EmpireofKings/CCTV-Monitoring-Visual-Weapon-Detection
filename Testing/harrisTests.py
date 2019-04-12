# Ben Ryan C15507277

import cv2
import easygui
import numpy as np


def run():
	filename = easygui.fileopenbox('Choose and image')
	img = cv2.imread(filename)

	imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	harris = cv2.cornerHarris(imgGray, 2, 7, 0.05)
	harris = cv2.dilate(harris, None)
	img[harris > 0.01 * harris.max()] = [0, 0, 255]

	cv2.imshow('Detected points in red', img)
	cv2.waitKey(0)
