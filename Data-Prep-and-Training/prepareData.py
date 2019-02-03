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

#MEMORY ISSUES, SPLIT IN TO MULTIPLE FUN
def prepare(files):
	with tf.Session().as_default():
		frameCount = 1
		while len(files) != 0:
			file = random.choice(files)

			augCount = file.get("augmentCounter")
			label = file.get("label")
			path = file.get("path")

			img = tf.read_file(path)
			origTensor = None

			if '.bmp' in path:
				origTensor = tf.image.decode_bmp(img, channels=3)
			elif '.jpg' in path or 'jpeg' in path:
				origTensor = tf.image.decode_jpeg(img, channels=3)
			else:
				print("Error decoding image")

			origTensor = tf.image.convert_image_dtype(origTensor, dtype=tf.float32)
			origTensor = tf.image.resize_images(origTensor, (144, 256))

			if augCount == 4: #original
				augmentedTensor = origTensor
				file["augmentCounter"] -= 1

			elif augCount == 3: #brightened
				augmentedTensor = tf.image.random_brightness(origTensor, 0.75)
				file["augmentCounter"] -= 1

			elif augCount == 2: #darkened
				augmentedTensor = tf.image.random_saturation(origTensor, 0.1, 0.3)
				file["augmentCounter"] -= 1

			elif augCount == 1: #flipped
				augmentedTensor = tf.image.flip_left_right(origTensor)
				files.remove(file)

			else:
				print("Error in augment counter")
				sys.exit()

			finalTensor = tf.clip_by_value(augmentedTensor, 0.0, 1.0)

			path = "./Prepared-Data/"+str(frameCount)+"_"+str(augCount)+"_"+str(label)
			print(path)
			fp = open(path, 'wb')
			fp.write(finalTensor.eval())
			fp.close()

			frameCount += 1
		print("Finished.")

if __name__ == '__main__':
	print("Working...")
	removeExistingBatches()
	folders = getFolders()
	files = getFiles(folders)
	# read(files)
	prepare(files)
