import cv2
import numpy as np
import easygui


def run():
	filename = easygui.fileopenbox('Choose an image')

	imgX = cv2.imread(filename)
	imgY = imgX.copy()

	imgGray = cv2.cvtColor(imgX, cv2.COLOR_BGR2GRAY)
	imgY = imgX.copy()
	imgTot = imgX.copy()
	sobelX = cv2.Sobel(imgGray, cv2.CV_64F, 1, 0, 3)
	sobelY = cv2.Sobel(imgGray, cv2.CV_64F, 0, 1, 3)

	imgX[sobelX > 0.1 * sobelX.max()] = [0, 0, 255]
	imgY[sobelY > 0.1 * sobelY.max()] = [0, 0, 255]

	imgTot[sobelX > 0.1 * sobelX.max()] = [0, 0, 255]
	imgTot[sobelY > 0.1 * sobelY.max()] = [0, 0, 255]

	cv2.imshow('Detected edges in red (Sobel X)', imgX)
	cv2.imshow('Detected edges in red (Sobel Y)', imgY)
	cv2.imshow("Detected edges in red (X + Y)", imgTot)

	cv2.waitKey(0)
