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
from sklearn.utils import class_weight as classWeight
import tensorflow as tf
from tensorflow.keras.layers import Conv2D, Dense, Flatten, MaxPooling2D, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import ModelCheckpoint, TensorBoard
from tensorflow.keras.utils import Sequence
from tensorflow.keras import regularizers
import tensorflow.keras.backend as K
import examineBatchContent as exBC

#os.environ['CUDA_VISIBLE_DEVICES'] = '-1' #uncomment to force CPU to be used

rootFolderGCP = "../../../../mnt/temp/"
rootFolderLocal = "C:/Dataset/"


#controls flow
def main():
	#setup session
	config = tf.ConfigProto()
	config.gpu_options.allow_growth = True  # dynamically grow the memory used on the GPU
	sess = tf.Session(config=config)
	tf.keras.backend.set_session(sess)

	#get and shuffle batch paths
	datasetPaths= exBC.preparePaths(rootFolderLocal+'Prepared-Data')
	#datasetPaths= exBC.preparePaths(rootFolderGCP+'Prepared-Data')

	random.shuffle(datasetPaths)
	batchAmt = len(datasetPaths)

	testAmt = math.ceil(batchAmt * .1)

	#5% set aside for testing
	testingPaths = datasetPaths[:testAmt]
	trainingPaths = datasetPaths[testAmt:]

	writeVideo(testingPaths)
	print("Test Video Written")

	#prepare the model
	untrainedModel = prepModel((64, 64, 3))
	untrainedModel.summary()

	# train the model
	trainedModel = trainModel(trainingPaths, testingPaths, untrainedModel)
	print("model training finished")
	# save the model for the server
	trainedModel.save("model.h5")
	print("Model Saved")

	testModel(testingPaths, trainedModel)

	print("Complete")


def writeVideo(batches):
	#fps does not matter here as it will be displayed frame by frame for demoing
	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	outStream = cv2.VideoWriter('./testData.mp4', fourcc, fps=30.0, frameSize=(64, 64))

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
	model.add(Conv2D(32, (3,3), activation='relu', padding='same', input_shape=shape))
	model.add(Conv2D(32, (3,3), activation='relu'))
	model.add(MaxPooling2D(pool_size=(2, 2)))
	model.add(Dropout(0.25))

	# model.add(Conv2D(64, (3,3), activation='relu', padding='same', input_shape=shape, kernel_regularizer=regularizers.l2(0.01)))
	# model.add(Conv2D(64, (3,3), activation='relu'))
	# model.add(MaxPooling2D(pool_size=(2, 2)))
	# model.add(Dropout(0.25))

	model.add(Conv2D(64, (3,3), activation='relu', padding='same'))
	model.add(Conv2D(64, (3,3), activation='relu'))
	model.add(MaxPooling2D(pool_size=(2, 2)))
	model.add(Dropout(0.25))

	model.add(Conv2D(128, (3,3), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01)))
	model.add(Conv2D(128, (3,3), activation='relu'))
	model.add(MaxPooling2D(pool_size=(2, 2)))
	model.add(Dropout(0.25))

	#fully connected layers
	model.add(Flatten())
	model.add(Dense(4608, activation='relu', kernel_regularizer=regularizers.l2(0.01)))
	#model.add(Dense(512, activation='relu'))
	model.add(Dropout(0.25))
	model.add(Dense(12, activation='sigmoid'))

	#precision = keras_metrics.precision(label=1)
	#recall = keras_metrics.recall(label=0)

	model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])

	return model

#trains provided model on provided batches
def trainModel(trainingData, validationData, model):

	checkpointCB = ModelCheckpoint("../Checkpoints/model{epoch:02d}.hdf5")
	tensorBoardCB = TensorBoard(log_dir="./logs", write_images=True)


	trainSteps = len(trainingData)
	validateSteps = len(validationData)

	model.fit_generator(generator = DataSequence(trainingData), steps_per_epoch = trainSteps,
					    validation_data = DataSequence(validationData), validation_steps = validateSteps,
						class_weight = getClassWeights(trainingData), epochs = 30,
						callbacks = [checkpointCB, tensorBoardCB],
						max_queue_size = 500, workers = 20, shuffle = True,)

	return model

def getClassWeights(data):

	allLabels = []
	for paths in data:
		labelsPath = paths.get("labels")
		labels = np.load(labelsPath)
		for label in labels:
			allLabels.append(label)

	intLabels = [label.argmax() for label in allLabels]

	weights = classWeight.compute_class_weight('balanced', np.unique(intLabels), intLabels)
	weights = dict(enumerate(weights))

	return weights

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

		# for i in range(len(data)):
		# 	image = data[i]
		# 	predicted = predictions[i]
		# 	image = cv2.resize(image, (640,360))
		# 	cv2.imshow(str(predicted), image)
		# 	cv2.waitKey(0)
		# 	cv2.destroyAllWindows()

		for item in predictions:
			highest = np.argmax(item)
			if item[highest] > 0.5:
				item[highest] = 1.
			else:
				item[highest] = 0.

			for cat in range(len(item)):
				if cat != highest:
					item[cat] = 0.

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

def cifarMain():
	(x_train, y_train), (x_test, y_test) = tf.keras.datasets.cifar10.load_data()

	newXT = []
	print(np.shape(x_train))
	for im in x_train:
		im = cv2.resize(im, (64, 64))
		newXT.append(im)

	newYT = []
	for im in x_test:
		im = cv2.resize(im, (64,64))
		newYT.append(im)

	x_train = np.array(newXT)
	x_test = np.array(newYT)
	print(np.shape(x_train))

	x_train, x_test = x_train / 255.0, x_test / 255.0
	y_train = tf.keras.utils.to_categorical(y_train)
	y_test = tf.keras.utils.to_categorical(y_test)


	model = prepModel((64,64,3))
	model.summary()
	model.fit(x_train, y_train, epochs=10)
	print(model.evaluate(x_test, y_test))

	return model

if __name__ == '__main__':
	main()
	#cifarMain()
