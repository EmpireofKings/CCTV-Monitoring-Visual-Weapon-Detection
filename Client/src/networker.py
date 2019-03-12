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


class Networker(Thread):
	def __init__(self, camera, display, mainDisplay):
		Thread.__init__(self)

		self.stop = False
		self.camera = camera
		self.display = display
		self.nextFrame = None
		self.mainDisplay = mainDisplay
		self.serverAddr = 'tcp://35.204.135.105'
		self.localAddr = 'tcp://127.0.0.1'
		self.initPort = ':5000'
		self.displayConn = self.displayConnector(display)
		self.mainDisplayConn = self.displayConnector(mainDisplay)
		self.mainDisplay = mainDisplay

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

		#logging.debug('Socket: %s, private %s, public %s, server %s', socket, privateKey, publicKey, serverKey)
		return socket, certHandler, ctxHandler

	def initialize(self, feedID):
		initSocket, frontCert, frontCtx = self.setupSocket('front', True)
		feedSocket, feedCert, feedCtx = self.setupSocket(feedID, False)

		publicKey, _ = feedCert.getKeyPair()
		initSocket.connect(self.localAddr + self.initPort)
		print("SENDING", feedID + '  ' + publicKey.decode('utf-8'))
		initSocket.send_string(feedID + '  ' + publicKey.decode('utf-8'))
		print("SENT WAITING")
		initData = initSocket.recv_string()
		print("RECEIVED", initData)
		parts = initData.split('  ')

		port = ':' + parts[0]
		serverKey = parts[1]
		logging.debug('Assigned Port: %s using server key %s', port, serverKey)

		feedCert.savePublicKey(serverKey)
		serverKey = feedCert.getEnrolledKeys()
		feedSocket.curve_serverkey = serverKey

		feedSocket.connect(self.localAddr + port)

		return feedSocket, feedCert, feedCtx

	def run(self):
		global mainFeedID
		feedID = str(self.camera.camID).replace(' ', '')
		feedID = feedID.replace('/', '')
		feedID = feedID.replace('\\', '')
		feedID = feedID.replace(':', '')

		socket, certHandler, ctxHandler = self.initialize(feedID)

		monitorSocket = socket.get_monitor_socket()
		monitor = Monitor(monitorSocket, feedID)
		monitor.setDaemon(True)
		monitor.start()

		while self.stop is False:
			if self.nextFrame is not None:
				frames = self.nextFrame
				socket.send(frames[0])
				result = socket.recv_string()

				# TODO SWAP BACK TO DECOUPLED MODE
				self.displayConn.emitFrame(frames[1])

				# if this display is the main, emit the frame signal to both displays
				if self.camera.camID == self.mainDisplay.camera.camID:
					self.mainDisplayConn.emitFrame(frames[1])
					self.mainDisplay.camera = self.camera

		socket.disable_monitor()
		socket.close()
		ctxHandler.cleanup()
		certHandler.cleanup()
		print("clean up finished")

	class displayConnector(QObject):
		newFrameSignal = Signal(QPixmap)

		def __init__(self, display):
			QObject.__init__(self)
			self.newFrameSignal.connect(display.updateDisplay)

		def emitFrame(self, pmap):
			self.newFrameSignal.emit(pmap)
