import numpy as np
import cv2
import os
import tensorflow as tf
from results_handler import ResultsHandler
from feed_process_helper import FeedProcessHelper
import easygui
import random
from sklearn.metrics import classification_report

def chooseModel():
	modelFile = easygui.fileopenbox()

	model = tf.keras.models.load_model(modelFile)

	return model

foldernegs = "D:/Dataset/To be refined/Negatives"
folderpistol = "D:/Dataset/To be refined/Pistol"

namesnegs = os.listdir(foldernegs)
namespistol = os.listdir(folderpistol)

files = []
for name in namesnegs:
	files.append(os.path.join(foldernegs, name))

for name in namespistol:
	files.append(os.path.join(folderpistol, name))

random.shuffle(files)

labels = []

for file in files:
	if "Negative" in file:
		labels.append(0)
	elif "Pistol" in file:
		labels.append(1)

model = chooseModel()

helper = FeedProcessHelper()

preds = []

total = len(files)
count = 1
for file in files:
	frame = cv2.imread(file)
	regions1, drawCoords1 = helper.extractRegions(frame, 2, (64, 64), True)
	regions2, drawCoords2 = helper.extractRegions(frame, 3, (64, 64), True)
	regions3, drawCoords3 = helper.extractRegions(frame, 4, (64, 64), True)
	regions4, drawCoords4 = helper.extractRegions(frame, 5, (64, 64), True)
	regions5, drawCoords5 = helper.extractRegions(frame, 6, (64, 64), True)
	regions6, drawCoords6 = helper.extractRegions(frame, 7, (64, 64), True)

	resultSets = []
	resultSets.append(np.around(model.predict(regions1)[:,11:], decimals=3))
	resultSets.append(np.around(model.predict(regions2)[:,11:], decimals=3))
	resultSets.append(np.around(model.predict(regions3)[:,11:], decimals=3))
	resultSets.append(np.around(model.predict(regions4)[:,11:], decimals=3))
	resultSets.append(np.around(model.predict(regions5)[:,11:], decimals=3))
	resultSets.append(np.around(model.predict(regions6)[:,11:], decimals=3))

	pos = False
	for set in resultSets:
		if np.amax(set) > .96:
			preds.append(1)
			pos = True
			break

	if pos is False:
		preds.append(0)

	index = len(preds) - 1
	count += 1

print(classification_report(np.asarray(labels), np.asarray(preds)))
