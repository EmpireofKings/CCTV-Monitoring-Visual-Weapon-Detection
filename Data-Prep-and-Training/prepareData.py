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
import easygui
import random
import _pickle as pickle
import sharedParams as sp

#controls the flow
def main():
	#get required folders
	positiveFolder, negativeFolder, preparedFolder = getFolders()
	
	#get desired ratio
	ratio = input("Enter positive to negative image ratio in this form - positive:negative")

	#check demo mode
	sp.DEMO_MODE = sp.activateDemoMode()

	positiveFiles = getFiles(positiveFolder)
	negativeFiles = getFiles(negativeFolder)
	
	prepare(positiveFiles, negativeFiles, preparedFolder, ratio)
	
	print("Data prepared")

#gets required folders from user
def getFolders():
	positive, negative, prepared = None, None, None
	
	while positive == None:
		print("\nPlease select the folder of positive images")
		positive = easygui.diropenbox()
		
	while negative == None:
		print("\nPlease select the folder of negative images")
		negative = easygui.diropenbox()
		
	while prepared == None:
		print("\nPlease select a folder to store prepared images")
		prepared = easygui.diropenbox()
		
	return positive, negative, prepared

#gets list of file paths from folder
def getFiles(folder):
	files = os.listdir(folder)
	
	count = 0
	for file in files:
		files[count] = folder + "\\" + file
		count += 1 
	
	return files

#prepares the data given to it
def prepare(positive, negative, prepared, ratio):
	posTotal = len(positive)
	negTotal = len(negative)
		
	posRatio, negRatio = ratio.split(":")
	
	posRatio = int(posRatio)
	negRatio = int(negRatio)
	posAmt, negAmt = 0, 0
	
	#find the most amount of images possible while maintaining ratio
	while posAmt < posTotal and negAmt < negTotal:
		posAmt += posRatio
		negAmt+= negRatio
		
	#correct the values
	posAmt = posAmt - posRatio
	negAmt = negAmt - negRatio
	
	#select the calculated amount from the original data
	#shuffle first so each image gets fair chance to be included
	random.shuffle(positive)
	random.shuffle(negative)
	positive = positive[:posAmt]
	negative = negative[:negAmt]
	
	print("Original images being used: \nPositive: ", posAmt, "Negative: ", negAmt)
	print("\nTotal including augmented: \nPositive: ", str(posAmt*4), "Negative: ", str(negAmt*4))
	
	#combine the lists and shuffle to give a random spread of positive and negative examples
	comb = positive + negative
	random.shuffle(comb)
	
	data = []
	labels = []
	
	batchCount = 0
	imCount = 1
	
	print("\n\nPreparing...")
	for path in comb:
		image = cv2.imread(path)
		image = cv2.resize(image, sp.imageSize)
		
		#store original image
		data.append(image)

		lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB) #convert to HSV colour space
		l, a ,b = cv2.split(lab)#split channels
		avgV = np.mean(l) #get avg brigtness
		adj = int(avgV*.85) #get 85% as value to adjust brightness by
		
		#adjust brightness channel up and down
		lup = cv2.add(l, adj)
		ldown = cv2.add(l, -adj)
		
		#merge adjusted channels
		brighter = cv2.merge((lup, a, b))
		darker = cv2.merge((ldown, a, b))
		
		brighter = cv2.cvtColor(brighter, cv2.COLOR_LAB2BGR)
		data.append(brighter)
		
		darker = cv2.cvtColor(darker, cv2.COLOR_LAB2BGR)
		data.append(darker)
		
		#mirror the image horizontally
		flipped = cv2.flip(image, 1)
		data.append(flipped)
		
		#add 4 labels for as there are 4 augmentations
		if "Positive" in path:
			for _ in range(0,4): labels.append(1)
		elif "Negative" in path:
			for _ in range(0,4): labels.append(0)
			
		#if we have matched the max batch size or the total image count pickle and save the batch
		if len(data) >= sp.batchSize or imCount == len(comb):
			dataArr = np.asarray(data)
			labelsArr = np.asarray(labels)

			dataTup = (dataArr, labelsArr)
				
			file = open(prepared + "\\batch_" + str(batchCount), "wb")
			pickle.dump(dataTup, file)
			file.close()
			
			data = []
			labels = []
			
			batchCount += 1
		
		imCount +=1
		
		if sp.DEMO_MODE == True:
			image = cv2.resize(image, sp.displaySize)
			brighter = cv2.resize(brighter, sp.displaySize)
			darker = cv2.resize(darker, sp.displaySize)
			flipped = cv2.resize(flipped, sp.displaySize)
			
			cv2.imshow("Original", image)
			cv2.imshow("Brighter", brighter)
			cv2.imshow("Darker", darker)
			cv2.imshow("Flipped", flipped)
			cv2.waitKey(0)
			cv2.destroyAllWindows()

if __name__ == '__main__':
	main()