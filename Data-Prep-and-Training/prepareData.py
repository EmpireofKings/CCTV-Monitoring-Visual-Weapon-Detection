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
from pprint import pprint
import tensorflow as tf

from terminator import Terminator

rootFolderGCP = "../../../../mnt/temp/"
rootFolderLocal = "C:/Dataset/"

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

def removeExistingBatches(rootFolder):
	folder = rootFolder+"Prepared-Data/"
	files = os.listdir(folder)

	for file in files:
		os.remove(folder + '/' + file)

	if os.path.isfile(rootFolder+'resumeData.pickle'):
		os.remove(rootFolder+'resumeData.pickle')

#gets required folders from user
def getFolders(rootFolder):
	basePath = rootFolder+'Unrefined/'
	basePath = rootFolder+'Refined/'

	negativePath = basePath + 'Negatives'
	extraNeg = basePath + 'ExtraNeg'
	knifePath = basePath + 'Knife'
	pistolPath = basePath + 'Pistol'
	#riflePath = basePath + 'Rifle'
	#shotgunPath = basePath + 'Shotgun'
	#submachineGunPath = basePath +'SubmachineGun'

	folders = [knifePath, pistolPath] #flePath, shotgunPath, submachineGunPath)

	for i in range(10):
		cifarPath = basePath + "cifar" + str(i)
		folders.append(cifarPath)

	return folders

#gets list of file paths from folder
def getFiles(folders):
	fileData = []
	for folder in folders:
		files = os.listdir(folder)

		if "Neg" in folder:
			random.shuffle(files)
			files = files[:1000]

		print("From", folder, str(len(files)))

		for file in files:
			path = folder + "/" + file

			label = [0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.] #nothing
			#decide label:
			if "Knife" in folder:
				label[10] = 1.
			elif "Pistol" in folder:
				label[11] = 1.
			elif "cifar" in folder:
				l = folder[len(folder)-1]
				label[int(l)] = 1.
			#elif "Rifle" in folder or "Shotgun" in folder or "SubmachineGun" in folder:
			#	label = 3 #LONG GUNS

			#file path, augmentCounter, label
			fileData.append({ "path" : path,
							  "augmentCounter": 0,
							  "label" : label })

	random.shuffle(fileData)

	return fileData

def getResumeData(rootFolder):
	if os.path.isfile(rootFolder+"resumeData.pickle"):
		with open(rootFolder+"resumeData.pickle", 'rb') as fp:
			resumeData = pickle.load(fp)

			return resumeData[0], resumeData[1], resumeData[2], resumeData[3]
	else:
		print("No resume data found")
		sys.exit()

def prepare(files, rootFolder, terminator, partialData = [], partialLabels = [],  batchCount = 1):
	data = partialData
	labels = partialLabels

	batchSize = 64

	expectedAmt = int(math.floor(((len(files))/batchSize)))

	while len(files) != 0:
		#if being told to terminate, save required data to restart at same place
		if terminator.isTerminating():
			resumeData = (files, data, labels, batchCount)

			with open(rootFolder+"resumeData.pickle", 'wb') as fp:
				pickle.dump(resumeData, fp, protocol=4)

			sys.exit()

		file = random.choice(files)

		label = file.get("label")
		path = file.get("path")

		orig = cv2.imread(path)

		orig = cv2.resize(orig, (64, 64))
		# augmented1 = adjustBrightness(orig.copy(), 1)
		# augmented2 = adjustBrightness(orig.copy(), -1)
		# augmented3 = cv2.flip(orig.copy(), 1)

		files.remove(file)

		f1 = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB) / 255.0
		# f2 = cv2.cvtColor(augmented1, cv2.COLOR_BGR2RGB) / 255.0
		# f3 = cv2.cvtColor(augmented2, cv2.COLOR_BGR2RGB) / 255.0
		# f4 = cv2.cvtColor(augmented3, cv2.COLOR_BGR2RGB) / 255.0

		data.append(f1)
		labels.append(label)

		# data.append(f2)
		# labels.append(label)
		#
		# data.append(f3)
		# labels.append(label)
		#
		# data.append(f4)
		# labels.append(label)

		if len(data) == batchSize:
			dataArr = np.array(data)
			labelsArr = np.array(labels)

			print("Batch", str(batchCount), "of", expectedAmt)

			data.clear()
			labels.clear()

			dataPath = rootFolder+"Prepared-Data/batch_" + str(batchCount) + "_data"
			labelsPath = rootFolder+"Prepared-Data/batch_" + str(batchCount) + "_labels"

			np.save(dataPath, dataArr , allow_pickle=True)
			np.save(labelsPath, labelsArr, allow_pickle=True)

			#with open(rootFolder+"Prepared-Data/batch_" + str(batchCount) + ".pickle", 'wb') as fp:
			#	pickle.dump((dataArr, labelsArr), fp)
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
		remainingfiles, partialData, partialLabels, batchCount = getResumeData(rootFolderLocal)
		prepare(remainingfiles, rootFolderLocal, terminator, partialData, partialLabels, batchCount)
		#prepare(remainingfiles, rootFolderGCP, terminator, partialData, partialLabels, batchCount)

	else:
		#double check the user gave the correct instruction before deleting everything
		ans = input("Are you sure you wish to start from the beginning. \nAll previously generated files will be permently deleted.(y/n)")

		if ans == 'Y' or ans == 'y':
			removeExistingBatches(rootFolderLocal)
			#removeExistingBatches(rootFolderGCP)
		else:
			sys.exit()

		folders = getFolders(rootFolderLocal)
		#folders = getFolders(rootFolderGCP)
		files = getFiles(folders)
		prepare(files, rootFolderLocal, terminator)
		#prepare(files, rootFolderGCP, terminator)
