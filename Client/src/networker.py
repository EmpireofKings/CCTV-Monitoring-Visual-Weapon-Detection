import os
import shutil
import sys
from threading import Thread
import time
import logging

import zmq
import zmq.auth
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from zmq.auth.thread import ThreadAuthenticator

from monitor import Monitor
from context_handler import ContextHandler
from certificate_handler import CertificateHandler
from terminator import Terminator
import uuid
from collections import deque
import _pickle as pickle
import cv2
import numpy as np
from connectors import DisplayConnector, GenericConnector
from notify_run import Notify


class Networker(Thread):
	def __init__(
		self, camera=None, display=None, mainDisplay=None,
		deferredMode=False, filePath=None, layoutHandler=None):
		Thread.__init__(self)

		self.layoutHandler = layoutHandler

		if self.layoutHandler is not None:
			self.updateConnector = GenericConnector(layoutHandler.updateLayout)
			#self.setAlertConnector = GenericConnector(layoutHandler.setAlert)

		self.end = False
		self.frames = deque()
		self.nextFrame = None

		self.camera = camera
		self.display = display
		self.deferredMode = deferredMode
		self.filePath = filePath

		if display is not None:
			self.displayConn = DisplayConnector(display)
			self.mainDisplayConn = DisplayConnector(mainDisplay)
			self.mainDisplay = mainDisplay

		self.serverAddr = 'tcp://35.204.135.105'
		self.localAddr = 'tcp://127.0.0.1'
		self.mainAddr = self.localAddr
		self.initPort = ':5000'

		self.total = 0

	def setupSocket(self, certID, serverKey=True):
		certHandler = CertificateHandler(certID, 'client')
		ctxHandler = ContextHandler(certHandler.getEnrolledKeysPath())

		context = ctxHandler.getContext()
		socket = context.socket(zmq.REQ)

		monitorSocket = socket.get_monitor_socket()
		monitor = Monitor(monitorSocket, certID)
		monitor.setDaemon(True)
		monitor.start()

		if certID != 'front':
			certHandler.prep()

		publicKey, privateKey = certHandler.getKeyPair()

		if serverKey:
			serverKey = certHandler.getEnrolledKeys()
			socket.curve_serverkey = serverKey

		socket.curve_secretkey = privateKey
		socket.curve_publickey = publicKey

		return socket, certHandler, ctxHandler

	def initialize(self, feedID):
		initSocket, frontCert, frontCtx = self.setupSocket('front', True)
		feedSocket, feedCert, feedCtx = self.setupSocket(feedID, False)

		publicKey, _ = feedCert.getKeyPair()
		initSocket.connect(self.mainAddr + self.initPort)
		initSocket.send_string(feedID + '  ' + publicKey.decode('utf-8'))
		initData = initSocket.recv_string()
		parts = initData.split('  ')

		port = ':' + parts[0]
		serverKey = parts[1]
		logging.debug('Assigned Port: %s using server key %s', port, serverKey)

		feedCert.savePublicKey(serverKey)
		serverKey = feedCert.getEnrolledKeys()
		feedSocket.curve_serverkey = serverKey

		feedSocket.connect(self.mainAddr + port)

		return feedSocket, feedCert, feedCtx

	def run(self):
		if self.camera is not None:
			feedID = str(self.camera.camID)
		elif self.deferredMode:
			feedID = self.filePath

		feedID = feedID.replace(' ', '')
		feedID = feedID.replace('/', '')
		feedID = feedID.replace('\\', '')
		feedID = feedID.replace(':', '')
		feedID = feedID.replace('.', '')
		feedID = feedID + str(uuid.uuid4().hex)

		socket, certHandler, ctxHandler = self.initialize(feedID)

		monitorSocket = socket.get_monitor_socket()
		monitor = Monitor(monitorSocket, feedID)
		monitor.setDaemon(True)
		monitor.start()

		terminator = Terminator.getInstance()
		deferredTimer = time.time()

		results = []

		notify = Notify()
		notifyTimer = time.time()

		while not terminator.isTerminating() and self.end is False or (self.end is True and len(self.frames) > 0):
			if self.nextFrame is not None or len(self.frames) > 0:
				self.total += 1
				deferredTimer = time.time()

				if self.deferredMode:
					frame = self.frames.pop()
				else:
					frame = self.nextFrame
					self.nextFrame = None

				processFrame = frame[0]
				displayFrame = frame[1]
				socket.send(processFrame)

				serial = socket.recv()

				result = pickle.loads(serial)

				if result[0] > 0.99 and not self.deferredMode:
					self.camera.alert = True
					alertTimer = time.time()
					self.updateConnector.emitSignal()

					if notify is not None and time.time() - notifyTimer >= 30:
							notify.send(
								'Weapon detected at level ' +
								str(self.camera.levelID) + ' ' +
								self.camera.location)
							notifyTimer = time.time()

				if not self.deferredMode:
					if self.camera.alert:
						if time.time() - alertTimer >= 60:
							self.camera.alert = False
							self.updateConnector.emitSignal()

				boundingBoxes = result[1]

				if boundingBoxes != []:
					height, width, _ = np.shape(displayFrame)
					for box in boundingBoxes:
						x, y, w, h = box
						x = int(self.scale(x, 0, 1, 0, width))
						y = int(self.scale(y, 0, 1, 0, height))
						w = int(self.scale(w, 0, 1, 0, width))
						h = int(self.scale(h, 0, 1, 0, height))

						cv2.rectangle(
							displayFrame, (x, y), (x + w, y + h), (0, 255, 0), 2)

				# # if this display is the main, emit the frame signal to both displays

				if not self.deferredMode:
					mainCam = self.layoutHandler.drawSpace.controls.getSelectedCamera()
					if self.camera.camID == mainCam.camID:
						self.mainDisplayConn.emitFrame(displayFrame)
						#self.mainDisplay.camera = self.camera
				else:
					results.append(result)

			elif (time.time() - deferredTimer) > 5 and self.deferredMode:
				socket.send_string("wait")
				timer = time.time()
				received = socket.recv_string()
				if received != 'ok':
					logging.error('Unexcepted message %s', received)
			else:
				time.sleep(0.001)

		if self.deferredMode:
			with open('../Processed/' + self.filePath + '.result', 'wb') as fp:
				pickle.dump(results, fp, protocol=4)

		#socket.disable_monitor()
		try:
			socket.close()
			#ctxHandler.cleanup()
			certHandler.cleanup()
		except Exception as e:
			print("exception while ending", e)

	def scale(self, val, inMin, inMax, outMin, outMax):
		return ((val - inMin) / (inMax - inMin)) * (outMax - outMin) + outMin
