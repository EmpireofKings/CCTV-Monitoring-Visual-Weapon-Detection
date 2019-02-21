# Ben Ryan - C15507277 Final Year Project
# This script is used to train a neural network

# Steps:
# TODO

import math
import os
import random
import sys

import cv2
import keras_metrics
import numpy as np
from sklearn.metrics import classification_report, precision_score, recall_score, accuracy_score, f1_score
import tensorflow as tf
from tensorflow.keras.layers import Conv2D, Dense, Flatten, MaxPooling2D
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.utils import Sequence
import tensorflow.keras.backend as K
import examineBatchContent as exBC

#os.environ['CUDA_VISIBLE_DEVICES'] = '-1' #uncomment to force CPU to be used

#controls flow
def main():
	#setup session
	config = tf.ConfigProto()
	config.gpu_options.allow_growth = True  # dynamically grow the memory used on the GPU
	sess = tf.Session(config=config)
	tf.keras.backend.set_session(sess)

	#get and shuffle batch paths
	datasetPaths= exBC.preparePaths('../../../../mnt/temp/Prepared-Data')
	random.shuffle(datasetPaths)
	batchAmt = len(datasetPaths)

	testAmt = math.ceil(batchAmt * .05)

	#5% set aside for testing
	testingPaths = datasetPaths[:testAmt]
	trainingPaths = datasetPaths[testAmt:]

	writeVideo(testingPaths)
	print("Test Video Written")

	#prepare the model
	untrainedModel = prepModel((144, 256, 3))
	untrainedModel.summary()

	#train the model
	trainedModel = trainModel(trainingPaths, untrainedModel)
	print("model training finished")
	#save the model for the server
	trainedModel.save("model.h5")
	print("Model Saved")

	testModel(testingPaths, trainedModel)

	print("Complete")


def writeVideo(batches):
	#fps does not matter here as it will be displayed frame by frame for demoing
	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	outStream = cv2.VideoWriter('./testData.mp4', fourcc, fps=30.0, frameSize=(256, 144))

	for batch in batches:
		dataPath = batch.get("data")
		data = np.load(dataPath)

		for image in data:
			norm = cv2.normalize(image, None, alpha = 0, beta = 255, norm_type = cv2.NORM_MINMAX, dtype = cv2.CV_8U)
			outStream.write(norm)

	outStream.release()

#prepares model as specified
def prepModel(shape):
	model = Sequential()

	#convolutional/pooling layers
	model.add(Conv2D(64, (5,5), activation='relu', input_shape=shape))
	model.add(MaxPooling2D(pool_size=(5, 5)))
	model.add(Conv2D(32, (2,2), activation='relu'))
	model.add(Conv2D(16, (2,2), activation='relu'))
	model.add(Conv2D(8, (3,3), activation='relu'))
	model.add(MaxPooling2D(pool_size=(2, 2)))

	#fully connected layers
	model.add(Flatten())
	model.add(Dense(128, activation='relu'))
	model.add(Dense(64, activation='relu'))
	model.add(Dense(32, activation='relu'))
	model.add(Dense(2, activation='sigmoid'))


	#precision = keras_metrics.precision(label=1)
	#recall = keras_metrics.recall(label=0)

	model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=[precision, recall, 'categorical_accuracy'])

	return model


def precision(y_true, y_pred):
	true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
	predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
	precision = true_positives / (predicted_positives + K.epsilon())
	return precision


def recall(y_true, y_pred):
	true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
	possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
	recall = true_positives / (possible_positives + K.epsilon())
	return recall

#trains provided model on provided batches
def trainModel(batches, model):

	checkpointCB = ModelCheckpoint("../Checkpoints/model{epoch:02d}.hdf5")


	amt = len(batches)
	model.fit_generator(DataSequence(batches), shuffle = True, steps_per_epoch=amt, epochs=10, callbacks = [checkpointCB], max_queue_size = 50, use_multiprocessing = False, workers = 8)

	return model


class DataSequence(Sequence):
	def __init__(self, paths):
		Sequence.__init__(self)
		self.paths = paths

	def __len__(self):
		return len(self.paths)

	def __getitem__(self, idx):
		dataPath = self.paths[idx].get("data")
		labelsPath = self.paths[idx].get("labels")

		data = np.load(dataPath)
		labels = np.load(labelsPath)
		return (data, labels)



#evaluates the trained model
def testModel(paths, model):
	amt = len(paths)
	results = model.evaluate_generator(DataSequence(paths), steps=amt, max_queue_size=50, use_multiprocessing=False, workers = 9, verbose=1)


	true = []
	pred = []
	for path in paths:
		dataPath = path.get("data")
		labelsPath = path.get("labels")

		data = np.load(dataPath)
		labels = np.load(labelsPath)
		predictions = model.predict(data)

		for item in predictions:
			highest = np.argmax(item)
			if item[highest] > 0.5:
				item[highest] = 1
			else:
				item[highest] = 0

			for cat in range(len(item)):
				if cat != highest:
					item[cat] = 0

		for item in labels:
			#true.append([ item[0], item[1] ])
			true.append(item)
		for item in predictions:
			#pred.append([ int(item[0]), int(item[1]) ])
			pred.append(item)

	print(classification_report(np.asarray(true), np.asarray(pred)))
	#print(classification_report(true, pred))
	print(np.shape(true), np.shape(pred))
	print(results)
if __name__ == '__main__':
	main()
