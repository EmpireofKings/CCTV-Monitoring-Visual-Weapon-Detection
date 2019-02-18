# Ben Ryan - C15507277 Final Year Project
# This script is used to prepare the dataset for training
#
# Steps:
# TODO

import math
import os
import _pickle as pickle
import random
import sys
import time

import cv2
import numpy as np
import tensorflow as tf

from terminator import Terminator

def isResuming():
	if len(sys.argv) != 2:
		print("Usage:", sys.argv[0], "<state>")
		print("<state> options: resume, start")
		sys.exit()

	if sys.argv[1] == "resume":
		return True
	elif sys.argv[1] == "start":
		return False
	else:
		print("Argument error, must be \"resume\" or \"start\"")
		print("Provided argument =", sys.argv[1])
		sys.exit()

rootFolder = "../../../../mnt/temp/"

def removeExistingBatches():
	folder = rootFolder+"Prepared-Data/"
	files = os.listdir(folder)

	for file in files:
		os.remove(folder + '/' + file)

	if os.path.isfile(rootFolder+'resumeData.pickle'):
		os.remove(rootFolder+'resumeData.pickle')

#gets required folders from user
def getFolders():
	basePath = rootFolder+'Dataset/'
	negativePath = basePath + 'Negatives'
	knifePath = basePath + 'Knives'
	pistolPath = basePath + 'Pistol'
	riflePath = basePath + 'Rifle'
	shotgunPath = basePath + 'Shotgun'
	submachineGunPath = basePath +'SubmachineGun'

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
			path = folder + "/" + file

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

def getResumeData():
	if os.path.isfile(rootFolder+"resumeData.pickle"):
		with open(rootFolder+"resumeData.pickle", 'rb') as fp:
			resumeData = pickle.load(fp)

			return resumeData[0], resumeData[1], resumeData[2], resumeData[3]
	else:
		print("No resume data found")
		sys.exit()

def prepare(files, terminator, partialData = [], partialLabels = [],  batchCount = 0):
	data = partialData
	labels = partialLabels
	batchSize = 64

	expectedAmt = int(math.ceil((len(files)*4)/batchSize))

	while len(files) != 0:
		#if being told to terminate, save required data to restart at same place
		if terminator.isTerminating():
			resumeData = (files ,data, labels, batchCount)

			with open(rootFolder+"resumeData.pickle", 'wb') as fp:
				pickle.dump(resumeData, fp, protocol=4)

			sys.exit()

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

			print("Batch Number", str(batchCount), "of", expectedAmt, "(Total not accurate if resumed)")

			data.clear()
			labels.clear()

			dataPath = rootFolder+"Prepared-Data/batch_" + str(batchCount) + "_data"
			labelsPath = rootFolder+"./Prepared-Data/batch_" + str(batchCount) + "_labels"

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
	terminator = Terminator()

	if isResuming():
		remainingfiles, partialData, partialLabels, batchCount = getResumeData()
		prepare(remainingfiles, terminator, partialData, partialLabels, batchCount)
	else:
		#double check the user gave the correct instruction before deleting everything
		ans = input("Are you sure you wish to start from the beginning. \nAll previously generated files will be permently deleted.(y/n)")

		if ans == 'Y' or ans == 'y':
			removeExistingBatches()
		else:
			sys.exit()

		folders = getFolders()
		files = getFiles(folders)
		prepare(files, terminator)
