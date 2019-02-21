import numpy as np
import cv2
import requests
import csv

def getImages(links):	
	print("TOTAL: ", len(links))
	file = open("./counter.txt", 'r+')
	counter = int(file.read(10))
	print("Starting at", counter)
			
	#cut already completed links out
	links = links[counter:]
	print("AFTER CUT:", len(links))
	
	for link in links:
		img = requests.get(link).content
		
		img = np.fromstring(img, np.uint8)
		img = cv2.imdecode(img, cv2.IMREAD_COLOR)
		
		parts = link.split('/')
		name = parts[len(parts)-1]
		
		imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		mean = np.mean(imgGray)
		h, w = np.shape(imgGray)
		
		if not (mean > 150 or h > w or h < 210 or w < 210):
			cv2.imwrite("./cleaned/" + name, img)
			
		#so we can pick up from where we left off, in case of crash
		counter += 1
		file.seek(0)
		file.write(str(counter))
		
	file.close()
			
if __name__ == '__main__':
	file = open("./imageLinks.txt", 'r')
	reader = csv.reader(file)
	
	links = []
	for row in reader:
		links.append(row[0])

	getImages(links)