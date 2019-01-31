# Ben Ryan - C15507277 Final Year Project
# This script is used to prepare the dataset for training
#
# Steps:
#	Request the location of positives, negatives and the desired ratio between them
#	Randomize the order
#	Augment each original, flipped, brightened and darkened
#	Place in 4D tensors of shape (64, 100, 100, 3)
#	Serialize each batch along with labels.

import cv2
import numpy as np
import os
import sys
import easygui
import random
import math
import gc
import _pickle as pickle
import time
import tracemalloc
import linecache

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

file = None
augCount = None
label = None
original = None
resized = None
save = None
save1 = None

#MEMORY ISSUES, SPLIT IN TO MULTIPLE FUN
def prepare(files):
	data = []
	labels = []

	batchSize = 128
	batchCount = 0

	tracemalloc.start()


	while len(files) != 0:
		file = random.choice(files)
		augCount = file.get("augmentCounter")
		label = file.get("label")

		original = cv2.imread(file.get("path"))
		resized = cv2.resize(original, (256, 144))

		if augCount == 4: #original
			save = original
			file["augmentCounter"] -= 1

		elif augCount == 3: #brightened
			save = adjustBrightness(resized, 1)
			file["augmentCounter"] -= 1

		elif augCount == 2: #darkened
			save = adjustBrightness(resized, -1)
			file["augmentCounter"] -= 1

		elif augCount == 1: #flipped
			save = cv2.flip(resized, 1)
			files.remove(file)

		else:
			print("Error in augment counter")
			sys.exit()

		save1 = cv2.cvtColor(save, cv2.COLOR_BGR2RGB)
		data.append(save1)
		labels.append(label)

		if len(data) == batchSize:
			saveBatch(data, labels, batchCount)

			data.clear()
			labels.clear()

			batchCount += 1

	#	gc.collect()

	print("Finished.")

def saveBatch(data, labels, batchCount):
	print("Batch", batchCount, "Data", len(data), "labels", len(labels))
	dataArr = np.asarray(data)
	labelsArr = np.asarray(labels)

	file = open("./Prepared-Data/batch_" + str(batchCount), "wb")
	pickle.dump((dataArr, labelsArr), file)
	file.close()

	os.system('cls')
	snap = tracemalloc.take_snapshot()
	display_top(snap)

# CREDIT: https://stackoverflow.com/questions/552744/how-do-i-profile-memory-usage-in-python
def display_top(snapshot, key_type='lineno', limit=3):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        print("#%s: %s:%s: %.1f KiB"
              % (index, filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))



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
	prepare(files)
