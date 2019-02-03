# Ben Ryan - C15507277 Final Year Project
# Testing script used to ensure the batch files produced by prepareData.py
# are as expected i.e. right amount of images per batch, corresponding labels are correct etc.

import os
import cv2
import numpy as np

def preparePaths(folder):
	files = os.listdir(folder)

	totalBatches = int(len(files)/2)

	batchPaths = []
	for batch in range(1, totalBatches):
		data = folder + "/batch_" + str(batch) + "_data.npy"
		labels = folder + "/batch_" + str(batch) + "_labels.npy"

		batchPaths.append({"data" : data, "labels" : labels})

	return batchPaths


def view(batchPaths):
	for batch in batchPaths:
		dataPath = batch.get("data")
		labelsPath = batch.get("labels")

		data = np.load(dataPath)
		labels = np.load(labelsPath)

		print(np.shape(data), np.shape(labels))

		for i in range(len(data)):
			image = data[i]
			label = labels[i]

			cv2.imshow(str(label), image)
			cv2.waitKey(0)
			cv2.destroyAllWindows()

if __name__ == '__main__':
	batchPaths = preparePaths('./Prepared-Data')
	view(batchPaths)
