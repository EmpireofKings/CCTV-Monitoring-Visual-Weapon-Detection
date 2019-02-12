# Ben Ryan - C15507277 Final Year Project
# This script is used to train a neural network

# Steps:
# TODO

import math
import os
import random
import sys

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Conv2D, Dense, Flatten, MaxPooling2D
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import ModelCheckpoint

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
	datasetPaths= exBC.preparePaths('./Prepared-Data')
	random.shuffle(datasetPaths)
	batchAmt = len(datasetPaths)

	testAmt = math.ceil(batchAmt * .5)

	#5% set aside for testing
	testingPaths = datasetPaths[:testAmt]
	trainingPaths = datasetPaths[testAmt:]

	#prepare the model
	untrainedModel = prepModel((144, 256, 3))
	untrainedModel.summary()

	#train the model
	trainedModel = trainModel(trainingPaths, untrainedModel)
	testModel(testingPaths, trainedModel)

	#save the model for the server
	trainedModel.save("model.h5")

	print("Complete")

#prepares model as specified
def prepModel(shape):
	model = Sequential()

	#convolutional/pooling layers
	model.add(Conv2D(64, (5,5), activation='relu', input_shape=shape))
	# model.add(MaxPooling2D(pool_size=(5, 5)))
	# model.add(Conv2D(32, (2,2), activation='relu'))
	# model.add(Conv2D(16, (2,2), activation='relu'))
	#model.add(Conv2D(16, (3,3), activation='relu'))
	model.add(MaxPooling2D(pool_size=(2, 2)))

	#fully connected layers
	model.add(Flatten())
	# model.add(Dense(16, activation='relu'))
	model.add(Dense(8, activation='relu'))
	# model.add(Dense(, activation='relu'))
	model.add(Dense(4, activation='sigmoid'))

	model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy', 'categorical_accuracy'])

	return model

#trains provided model on provided batches
def trainModel(batches, model):

	checkpointCB = ModelCheckpoint("../Checkpoints/model{epoch:02d}-{val_loss:.2f}.hdf5")

	amt = len(batches)
	model.fit_generator(genData(batches),steps_per_epoch=amt, epochs=2, callbacks = [checkpointCB], use_multiprocessing = True, workers = 10, shuffle = True)

	return model

#yields one batch image-label pair at a time
def genData(paths):
	while True:
		#after all have been used shuffle
		random.shuffle(paths)
		for path in paths:
			dataPath = path.get("data")
			labelsPath = path.get("labels")

			data = np.load(dataPath)
			labels = np.load(labelsPath)

			yield((data, labels))

#evaluates the trained model
def testModel(paths, model):
	amt = len(paths)
	results = model.evaluate_generator(genData(paths), steps=amt, max_queue_size=1)

	print(results)

if __name__ == '__main__':
	main()
