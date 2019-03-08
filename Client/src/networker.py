import os
import shutil
import sys
from threading import Thread

import zmq
import zmq.auth
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from zmq.auth.thread import ThreadAuthenticator


class CertificateHandler():
	def __init__(self, id):
		self.id = id
		self.basePath = '../Certificates'
		self.publicFolderPath = self.basePath + '/Public-' + str(id) + '/'
		self.privateFolderPath = self.basePath + '/Private-' + str(id) + '/'
		self.publicFilePath = self.publicFolderPath + "client-" + self.id + ".key"
		self.privateFilePath = self.privateFolderPath + "client-" + self.id + ".key_secret"

	def _generateCertificates(self):
		if os.path.exists(self.basePath):
			shutil.rmtree(self.basePath)

		os.mkdir(self.basePath)
		os.mkdir(self.publicFolderPath)
		os.mkdir(self.privateFolderPath)

		public, private = zmq.auth.create_certificates(self.basePath, "client-" + self.id)
		print("PATHS:", public, private)
		shutil.move(public, self.publicFilePath)
		shutil.move(private, self.privateFilePath)

	def getCertificatesPaths(self):
		if not os.path.exists(self.publicFilePath) or not os.path.exists(self.privateFilePath):
			print("Generating new keys, clients will need access to public key.")
			self._generateCertificates()

		return self.publicFolderPath, self.privateFolderPath

	def getServerKey(self):
		serverKeyPath = '../server-front.key'
		
		if os.path.exists(serverKeyPath):
			return serverKeyPath
		else:
			print("Error: Missing Certificates at", serverKeyPath)
			sys.exit()


class Networker(Thread):
	def __init__(self, camera, display, mainDisplay):
		Thread.__init__(self)

		self.stop = False
		self.camera = camera
		self.display = display
		self.nextFrame = None
		self.mainDisplay = mainDisplay


		# todo parameterise socket setup for client and server
		# decouple authenticator thread start and networke thread to handle address already in use
		# use secure sockets for each cam connection

	def initialize(self):
		serverAddr = 'tcp://35.204.135.105'
		localAddr = 'tcp://127.0.0.1'
		initPort = ':5000'

		certHandler = CertificateHandler(id="front")
		publicPath, privatePath = certHandler.getCertificatesPaths()
		serverPath = certHandler.getServerKey()

		context = zmq.Context.instance()
		auth = ThreadAuthenticator(context)
		auth.start()

		auth.configure_curve(domain='*', location=publicPath)

		initSocket = context.socket(zmq.REQ)
		privateFile = privatePath + "client-front.key_secret"
		publicKey, privateKey = zmq.auth.load_certificate(privateFile)
		initSocket.curve_secretkey = privateKey
		initSocket.curve_publickey = publicKey

		serverKey = zmq.auth.load_certificate(serverPath)[0]
		initSocket.curve_serverkey = serverKey
		initSocket.connect(localAddr + initPort)
		print("connected")

		initSocket.send_string(str(self.camera.id))

		mainPort = ':' + initSocket.recv_string()
		print(mainPort, self.camera.id)

	def connect(self, port):
		soocket = context.socket(zmq.REQ)
		socket.connect(localAddr + port)
		return socket

	def run(self):
		global mainFeedID
		port = self.initialize()
		socket = self.connect(port)

		while self.stop is False:
			if self.nextFrame is not None:
				frames = self.nextFrame

				socket.send(frames[0])

				result = socket.recv_string()
				print(self.camera.id, result)

				# self.display.newFrameSignal.emit(frames[1])

				# uf this display is the main, emit the frame signal to both displays
				# if self.camera.id == self.mainDisplay.camera.id:
				# 	self.mainDisplay.newFrameSignal.emit(frames[1])
				# 	self.mainDisplay.camera = self.camera
