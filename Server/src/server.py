#TODO

import base64 as b64
import os
import shutil
import socket as s
import sys
import threading
import time
from collections import deque
from threading import Thread

import numpy as np

import _pickle as pickle
import cv2
import tensorflow as tf
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator


class CertificateHandler():
	def __init__(self, id):
		self.id = id
		self.basePath = '../Certificates'
		self.publicFolderPath = self.basePath + '/Public-' + str(id) + '/'
		self.privateFolderPath = self.basePath + '/Private-' + str(id) + '/'
		self.publicFilePath = self.publicFolderPath + "server-" + self.id + ".key"
		self.privateFilePath = self.privateFolderPath + "server-" + self.id + ".key_secret"

	def _generateCertificates(self):
		if os.path.exists(self.publicFolderPath):
			shutil.rmtree(self.publicFolderPath)

		if os.path.exists(self.privateFolderPath):
			shutil.rmtree(self.privateFolderPath)

		if not os.path.exists(self.basePath):
			os.mkdir(self.basePath)

		os.mkdir(self.publicFolderPath)
		os.mkdir(self.privateFolderPath)

		public, private = zmq.auth.create_certificates(self.basePath, "server-" + self.id)
		print("PATHS:", public, private)
		shutil.move(public, self.publicFilePath)
		shutil.move(private, self.privateFilePath)

	def getCertificatesPaths(self):
		if not os.path.exists(self.publicFilePath) or not os.path.exists(self.privateFilePath):
			print("Generating new keys, clients will need access to public key.")
			self._generateCertificates()

		return self.publicFolderPath, self.privateFolderPath


class ContextHandler():
	def __init__(self, publicPath):
		self.__context = zmq.Context()
		self.__auth = ThreadAuthenticator(self.__context)
		self.__auth.start()
		self.__auth.configure_curve(domain='*', location=publicPath)

	def getContext(self):
		return self.__context

	def getAuth(self):
		return self.__auth

	def cleanup(self):
		self.__auth.stop()
		self.__context.destroy()


class Listener(Thread):
	def __init__(self, addr):
		Thread.__init__(self)

		certHandler = CertificateHandler(id="front")
		publicPath, privatePath = certHandler.getCertificatesPaths()

		self.ctxHandler = ContextHandler(publicPath)
		context = self.ctxHandler.getContext()
		# auth.allow('134.0.0.1')
		self.socket = context.socket(zmq.REP)

		privateFile = privatePath + "server-front.key_secret"
		publicKey, privateKey = zmq.auth.load_certificate(privateFile)
		self.socket.curve_secretkey = privateKey
		self.socket.curve_publickey = publicKey
		self.socket.curve_server = True

		print(publicKey)
		self.socket.bind(addr)

		print("Listening on", addr)

	def run(self):
		while True:
			received = self.socket.recv_string()

			print("New connection from ", received)
			handler = FeedHandler(received)
			handler.setDaemon(True)
			handler.start()

			assignedPort = handler.getPort()
			publicKey = handler.getPublicKey()

			self.socket.send_string(str(assignedPort) + " " + str(publicKey, 'utf-8'))


class FeedHandler(Thread):
	def __init__(self, feedID):
		Thread.__init__(self)

		self.certHandler = CertificateHandler(id=feedID)
		publicPath, privatePath = self.certHandler.getCertificatesPaths()

		self.ctxHandler = ContextHandler(publicPath)
		context = self.ctxHandler.getContext()

		self.socket = context.socket(zmq.REP)

		privateFile = privatePath + "server-" + feedID + ".key_secret"
		self.publicKey, privateKey = zmq.auth.load_certificate(privateFile)
		self.socket.curve_secretkey = privateKey
		self.socket.curve_publickey = self.publicKey
		self.socket.curve_server = True

		self.port = self.socket.bind_to_random_port('tcp://*')
		self.feedID = feedID

	def getPort(self):
		return self.port

	def getPublicKey(self):
		return self.publicKey

	def run(self):
		helper = Helper()
		global model
		global session
		global graph

		resultHandler = ResultsHandler(9, 30)
		# bgRemover = BackgroundRemover(feed)

		print("before set")
		self.socket.setsockopt(zmq.RCVTIMEO, 10000)
		print("after set")
		with session.as_default():
			with graph.as_default():
				while True:
					try:
						received = self.socket.recv_string()
					except:
						break
					jpegStr = b64.b64decode(received)
					jpeg = np.fromstring(jpegStr, dtype=np.uint8)
					frame = cv2.imdecode(jpeg, 1)

					regions, drawCoords = helper.extractRegions(frame, 3, (64,64), True)
					results = np.around(model.predict(regions)[:,10:], decimals=3)
					resultHandler.append(results)
					alert = resultHandler.assess()

					#frame = bgRemover.drawBoundingBox(frame)

					self.socket.send_string(str(alert))

		print("Ending thread", self.feedID)

class Helper():	
	def extractRegions(self, frame, gridSize, regionSize, prepare=True, offset=False, offsetX=0, offsetY=0):
		h, w, c = np.shape(frame)

		regionH = int(h/gridSize)
		regionW = int(w/gridSize)

		regions = []
		drawCoords = []
		for row in range(gridSize):
			regionY = row * regionH
			for col in range(gridSize):
				regionX = col * regionW

				region = frame[regionY: regionY + regionH, regionX:regionX + regionW]

				if offset:
					drawCoords.append((regionX + offsetX, regionY + offsetY, regionW, regionH))
				else:
					drawCoords.append((regionX, regionY, regionW, regionH))

				region = cv2.resize(region, regionSize)
				region = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)

				if prepare is True:
					region = region / 255.0

				regions.append(region)

		# if offset is False:
		# 	subX = int(regionW/2)
		# 	subWidth = w-subX
		# 	subY = int(regionH/2)
		# 	subHeight = h-subY
		# 	subImage = frame[subY:subHeight, subX:subWidth]
		# 	extraRegions, extraDraw = extractRegions(subImage, 2, (64,64), offset = True, offsetX = subX, offsetY = subY)

		# 	for count in range(len(extraRegions)):
		# 		regions.append(extraRegions[count])
		# 		drawCoords.append(extraDraw[count])

		return np.array(regions), drawCoords

	def drawResults(self, img, results, drawCoords, categories, all=False):
		for count in range(len(results)):
			regionResults = results[count]
			highest = np.argmax(regionResults)

			if regionResults[highest] > 0:
				label = categories[highest]
				regionX, regionY, regionW, regionH = drawCoords[count]
				cv2.rectangle(img, (regionX, regionY), (regionX+regionW, regionY+regionH), (0,0,255), 3)
				cv2.putText(img, label, (regionX+10, regionY+regionH-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
				cv2.putText(img, str(regionResults[highest]), (regionX+10, regionY+regionH-60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)


			elif all:
				label = "Clear"
				regionX, regionY, regionW, regionH = drawCoords[count]
				cv2.rectangle(img, (regionX, regionY), (regionX+regionW, regionY+regionH), (0,255,0), 1)

		return img

	def getDefaultModel(self, summary=False):
		path = "../../Decent Models\model-current.h5"

		model = tf.keras.models.load_model(path)
		
		if summary:
			model.summary()

		return model

class BackgroundRemover():
	def __init__(self, feed):
		self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(5,5))

		while feed.isOpened():
			check, frame = feed.read()
			
			if check:
				cv2.imshow("Press enter to capture background", frame)
				key = cv2.waitKey(0)
				
				if key == 13:
					gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
					blurred = cv2.GaussianBlur(gray, (5,5), 0)
					self.background = self.clahe.apply(blurred)
					break

	def drawBoundingBox(self, frame):
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		blurred = cv2.GaussianBlur(gray, (5, 5), 0)
		equalized = self.clahe.apply(blurred)

		diff = cv2.absdiff(equalized, self.background)
		_, binary = cv2.threshold(diff, 60, 255, cv2.THRESH_BINARY)
		structEl = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
		
		opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, structEl)

		_, contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		if len(contours) > 0:
			largest = max(contours, key=cv2.contourArea)

			x, y, w, h = cv2.boundingRect(largest)
			cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)

		return frame

class ResultsHandler():
	def __init__(self, amount, size):
		
		self.buffers = []
		for _ in range(amount):
			buf = self.ResultBuffer(size)
			self.buffers.append(buf)

	def getAverages(self):
		averages = []
		for buf in self.buffers:
			avg = buf.getAvg()
			averages.append(avg)

		return averages

	def getLengths(self):
		lengths = []
		for buf in self.buffers:
			l = len(buf)
			lengths.append(l)
		
		return lengths

	def __len__(self):
		return len(self.buffers)

	def append(self, results):
		for count in range(len(self.buffers)):
			buffer = self.buffers[count]
			resultSet = results[count]

			buffer.append(resultSet[0], resultSet[1])

	def assess(self):
		averages = self.getAverages()

		for avg in averages:
			if max(avg) > 0.95:
				return True


	class ResultBuffer():
		def __init__(self, size):
			self.knifeBuffer = deque(maxlen=size)
			self.pistolBuffer = deque(maxlen=size)

		def getAvg(self):
			knifeAvg = sum(self.knifeBuffer)/len(self.knifeBuffer)
			pistolAvg = sum(self.pistolBuffer)/len(self.pistolBuffer)

			return (knifeAvg, pistolAvg)

		def __len__(self):
			length = len(self.knifeBuffer)
			if length == len(self.pistolBuffer):
				return length
			else:
				return -1

		def append(self, knife, pistol):
			self.knifeBuffer.append(knife)
			self.pistolBuffer.append(pistol)
	

if __name__ == '__main__':
	responseQueues = {}
	helper = Helper()
	model = helper.getDefaultModel(summary=True)
	model._make_predict_function()
	session = tf.keras.backend.get_session()
	graph = tf.get_default_graph()
	graph.finalize()

	listener = Listener('tcp://0.0.0.0:5000')
	listener.start()
