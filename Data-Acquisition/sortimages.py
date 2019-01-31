import numpy as np
import cv2
import csv
import os

typeLocMap = {0:['./Data/Sorted/Pistol/', './Sort Files/pistols.txt'],
			  1:['./Data/Sorted/Rifle/', './Sort Files/rifles.txt'],
			  2:['./Data/Sorted/Shotgun/', './Sort Files/shotguns.txt'],
			  3:['./Data/Sorted/SubmachineGun/', './Sort Files/submachineguns.txt'],
			  4:['./Data/Sorted/other/', './Sort Files/other.txt'],
			  5:['delete','delete']}

imageDir = "./Data/Unsorted/"

def getSortLists():
	pistols = getList(typeLocMap[0][1])
	rifles = getList(typeLocMap[1][1])
	shotguns = getList(typeLocMap[2][1])
	submachineguns = getList(typeLocMap[3][1])
	other = getList(typeLocMap[4][1])

	return (pistols, rifles, shotguns, submachineguns, other)

def getList(path):
	file = open(path, 'r')
	reader = csv.reader(file)
	return next(reader)

def getImagePaths():
	files = os.listdir(imageDir)

	images = []
	for file in files:
		images.append(imageDir + file)

	return images

def sort(sortLists, images):
	for name in images:
		img = cv2.imread(name)
		result = findType(name, sortLists)

		if result is not None:
			# type, tag = askUser(img, name)
			# result = typeLocMap.get(type)[0]

			# only add if not empty string, empty for generic, ie no name
			# if tag != '' and type != 5:
				# file = open(typeLocMap.get(type)[1], 'a')
				# file.write((',' + tag).rstrip('\n'))
				# file.close()

				# sortLists = getSortLists()
			path = result + name[len(imageDir):]
			if result[:6] != 'delete':
				cv2.imwrite(path, img)

			os.remove(name)

def askUser(img, name):
	print("\n\nHow should this be sorted?\n" + name + "\n\nPistol = 0 \nRifle = 1 \nShotgun = 2 \nSubmachine gun = 3 \nOther = 4 \nDelete = 5")
	cv2.imshow(name, img)
	type = - 1

	while type < 0 or type > 5:
		type = cv2.waitKey(0) - 48

	cv2.destroyAllWindows()

	tag = input("What tag should this have?")

	return type, tag


def findType(name, sortLists):
	name = name.upper()
	for type in range(len(sortLists)):
		for model in sortLists[type]:
			model = model.upper()
			if model in name:
				path = typeLocMap.get(type)[0]
				return path

	return None
if __name__ == '__main__':
	sortLists = getSortLists()
	images = getImagePaths()
	sort(sortLists, images)
