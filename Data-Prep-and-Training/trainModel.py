# Ben Ryan - C15507277 Final Year Project
# This script is used to train a neural network

# Steps:
#	Get batch paths
#	Shuffle batches
#	Select 5% to set aside for testing
#	Write the testing batches to a video so it can be tested via server
#	Prepare the untrained model
#	Train model on training batches using generator
# 	Save trained model so it can be used on server

import os
#os.environ['CUDA_VISIBLE_DEVICES'] = '-1' #uncomment to force CPU to be used

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten, Dense, Conv2D, MaxPooling2D
import tensorflow as tf
import cv2
import numpy as np
import easygui
import _pickle as pickle
import random
import sharedParams as sp

#controls flow
def main():
	#setup session
	config = tf.ConfigProto()
	config.gpu_options.allow_growth = True  # dynamically grow the memory used on the GPU
	sess = tf.Session(config=config)
	tf.keras.backend.set_session(sess)
	
	#get and shuffle batch paths
	batches = getBatch()
	random.shuffle(batches)
	batchAmt = len(batches)
	
	if testAmt == 0:
		testAmt = 1
		
	#5% set aside for testing
	testingBatches = batches[:testAmt]
	trainingBatches = batches[testAmt:]
	
	#write testing images to video so it can be easily tested on the server
	writeVideo(testingBatches)
	print("Test video written")
	
	#prepare the model
	untrainedModel = prepModel(sp.imageShape)
	untrainedModel.summary()
	
	#train the model
	trainedModel = trainModel(trainingBatches, untrainedModel)
	testModel(testingBatches, trainedModel)
	
	#save the model for the server
	trainedModel.save("model.h5")

	print("Complete")

#gets batch paths from user
def getBatch():
	print("Select folder with prepared data")
	folder = easygui.diropenbox()
	
	files = os.listdir(folder)
	
	count = 0
	for file in files:
		files[count] = folder + "\\" + file
		count+=1
	return files

#writes set of batches to a video
def writeVideo(batches):
	#fps does not matter here as it will be displayed frame by frame for demoing
	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	outStream = cv2.VideoWriter('./testData.mp4', fourcc, fps=30.0, frameSize=sp.imageSize)
	
	for batch in batches:
		file = open(batch, "rb")
		data = pickle.load(file)
	
		images = data[0]
		
		for image in images:
			outStream.write(image)
			
	outStream.release()
	
#prepares model as specified	
def prepModel(shape):
	model = Sequential()
	
	#convolutional/pooling layers
	model.add(Conv2D(128, (3,3), activation='relu', input_shape=shape))
	model.add(MaxPooling2D(pool_size=(2, 2)))
	model.add(Conv2D(64, (3,3), activation='relu', input_shape=shape))
	model.add(Conv2D(32, (3,3), activation='relu'))
	model.add(Conv2D(16, (3,3), activation='relu'))
	model.add(MaxPooling2D(pool_size=(2, 2)))
	
	#fully connected layers
	model.add(Flatten())
	model.add(Dense(32, activation='relu'))
	model.add(Dense(16, activation='relu'))
	model.add(Dense(8, activation='relu'))
	model.add(Dense(1, activation='sigmoid'))
										
	model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

	return model

#trains provided model on provided batches
def trainModel(batches, model):
	amt = len(batches)
	model.fit_generator(genData(batches),steps_per_epoch=amt, epochs=10, verbose=1)

	return model
	
#yields one image-label pair at a time
def genData(batches):
	while True:
		random.shuffle(batches)
		for batch in batches:
			file = open(batch, "rb")
			data = pickle.load(file)
			yield(data)
	
#evaluates the trained model
def testModel(batches, model):
	amt = len(batches)
	results = model.evaluate_generator(genData(batches), steps=amt, max_queue_size=1)
	
	print(results)
	
if __name__ == '__main__':
	main()