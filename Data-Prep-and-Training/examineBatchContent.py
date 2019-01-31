# Ben Ryan - C15507277 Final Year Project
# Testing script used to ensure the batch files produced by prepareData.py
# are as expected i.e. right amount of images per batch, corresponding labels are correct etc.

import os
import cv2
import numpy as np
import easygui
import _pickle as pickle

print("Select folder")
folder = easygui.diropenbox()
files = os.listdir(folder)

#display each file in each batch
for file in files:
	path = folder + "\\" + file
	file = open(path, "rb")
	data = pickle.load(file)

	images = data[0]
	labels = data[1]

	print(np.shape(images), np.shape(labels))

	i = 0
	for image in images:
		cv2.imshow(str(labels[i]), image)
		cv2.waitKey(0)
		cv2.destroyAllWindows()
		i+=1
