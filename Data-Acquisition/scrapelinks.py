# Ben Ryan C15507277

import easygui
import requests
from bs4 import BeautifulSoup
import os
import csv


def getPageLinks():
	print("Where are the csv files?")
	folder = easygui.diropenbox()
	print("Working...")
	files = os.listdir(folder)

	links = []
	for path in files:
		path = folder + "\\" + path

		file = open(path, 'r')

		reader = csv.reader(file, delimiter=',')

		for row in reader:
			links.append(row[0])

	return links


def getImgLinks(links):
	print("Acquiring image links from", str(len(links)), "pages")
	imgLinks = []
	for link in links:
		response = requests.get(link)

		bs = BeautifulSoup(response.text, 'html.parser')
		tags = bs.find_all('img')

		for tag in tags:
			if '.jpg' in tag['src']:
				link = 'http://www.imfdb.org' + tag['src']
				imgLinks.append(link)

	print("Acquired", str(len(imgLinks)), "image links")

	return imgLinks

if __name__ == '__main__':
	links = getImgLinks(getPageLinks())

	file = open("./imageLinks.txt", 'w')

	for i in range(0, len(links)):
		if i == len(links) - 1:
			row = links[i]
		else:
			row = links[i] + ",\n"

		file.write(row)

	file.close()
