# Ben Ryan - C15507277 Final Year Project
# This script is used to prepare the dataset for training
#
# Steps:
#	Request the location of positives, negatives and the desired ratio between them
#	Randomize the order
#	Augment each original, flipped, brightened and darkened
#	Place in 4D tensors of shape (64, 100, 100, 3)
#	Serialize each batch along with labels.

import numpy as np
import os
import sys
import easygui
import random
import math
import gc
import _pickle as pickle
import time
import tensorflow as tf
import matplotlib.pyplot as plt
import cv2

def removeExistingBatches():
	folder = "./Prepared-Data"
	files = os.listdir(folder)

	for file in files:
		os.remove(folder + '/' + file)

#gets required folders from user
def getFolders():
	basePath = '../Data-Acquisition/Data/Sorted'
	negativePath = basePath + '/Negatives'
	knifePath = basePath + '/Knives'
	pistolPath = basePath + '/Pistol'
	riflePath = basePath + '/Rifle'
	shotgunPath = basePath + '/Shotgun'
	submachineGunPath = basePath +'/SubmachineGun'

	folders = ( negativePath, knifePath,
				pistolPath, riflePath,
				shotgunPath, submachineGunPath )

	return folders

#gets list of file paths from folder
def getFiles(folders):
	fileData = []
	for folder in folders:
		files = os.listdir(folder)

		for file in files:
			path = folder + "\\" + file

			label = -1
			#decide label:
			if "Negatives" in folder:
				label = 0 #NO WEAPON
			elif "Knives" in folder:
				label = 1 #KNIFE/SHARP OBJECT
			elif "Pistol" in folder:
				label = 2 #PISTOLS
			elif "Rifle" in folder or "Shotgun" in folder or "SubmachineGun" in folder:
				label = 3 #LONG GUNS

			if label == -1:
				print("Error: Label could not be determined for", file, "in", folder)
				sys.exit()

			#file path, augmentCounter, label
			fileData.append({ "path" : path,
							  "augmentCounter": 4,
							  "label" : label })

	random.shuffle(fileData)

	return fileData

def prepare(files):
	data = []
	labels = []
	batchSize = 128
	batchCount = 0

	while len(files) != 0:
		file = random.choice(files)

		augCount = file.get("augmentCounter")
		label = file.get("label")
		path = file.get("path")

		orig = cv2.imread(path)
		orig = cv2.resize(orig, (256, 144))

		if augCount == 4: #original
			augmented = orig
			file["augmentCounter"] -= 1

		elif augCount == 3: #brightened
			augmented = adjustBrightness(orig.copy(), 1)
			file["augmentCounter"] -= 1

		elif augCount == 2: #darkened
			augmented = adjustBrightness(orig.copy(), -1)
			file["augmentCounter"] -= 1

		elif augCount == 1: #flipped
			augmented = cv2.flip(orig.copy(), 1)
			files.remove(file)

		else:
			print("Error in augment counter")
			sys.exit()

		final = cv2.cvtColor(augmented, cv2.COLOR_BGR2RGB)
		final = final / 255.0

		data.append(final)
		labels.append(label)

		if len(data) == batchSize:
			dataArr = np.array(data)
			labelsArr = np.array(labels)
			print("Batch Number ", str(batchCount), np.shape(dataArr), np.shape(labelsArr))

			data.clear()
			labels.clear()

			dataPath = "./Prepared-Data/batch_" + str(batchCount) + "_data"
			labelsPath = "./Prepared-Data/batch_" + str(batchCount) + "_labels"

			np.save(dataPath, dataArr , allow_pickle=False)
			np.save(labelsPath, labelsArr, allow_pickle=False)

			batchCount += 1
	print("Finished.")


def adjustBrightness(img, mult):
	img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB) #convert to LAB colour space
	l, a ,b = cv2.split(img)#split channels
	avgV = np.mean(l) #get avg brigtness
	adjustVal = int(avgV*.85) * mult #get 85% as value to adjust brightness by

	#adjust brightness channel up
	lAdj = cv2.add(l, adjustVal)

	#merge adjusted channels
	img = cv2.merge((lAdj, a, b))
	img = cv2.cvtColor(img, cv2.COLOR_LAB2BGR)

	return img

if __name__ == '__main__':
	print("Working...")
	removeExistingBatches()
	folders = getFolders()
	files = getFiles(folders)
	# read(files)
	prepare(files)
