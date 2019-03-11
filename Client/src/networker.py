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
from zmq.utils.monitor import recv_monitor_message


class GlobalContextHandler():
	__instance = None

	def __init__(self, publicPath):
		if GlobalContextHandler.__instance is None:
			self.__context = zmq.Context()
			self.__auth = ThreadAuthenticator(self.__context)
			self.__auth.start()
			self.__auth.configure_curve(domain='*', location=publicPath)

			GlobalContextHandler.__instance = self
		else:
			return GlobalContextHandler.__instance

	@staticmethod
	def getInstance(publicPath):
		if GlobalContextHandler.__instance is None:
			GlobalContextHandler(publicPath)

		return GlobalContextHandler.__instance

	def getContext(self):
		return self.__context

	def getAuth(self):
		return self.__auth

	def cleanup(self):
		self.__auth.stop()
		self.__context.destroy()


class GlobalCertificateHandler():
	__instance = None

	def __init__(self):
		if GlobalCertificateHandler.__instance is None:
			self.id = 'front'
			self.basePath = '../Certificates'

			self.publicFolderPath = (
				self.basePath +
				'/Public-' +
				str(self.id) +
				'/')

			self.privateFolderPath = (
				self.basePath +
				'/Private-' +
				str(self.id) +
				'/')

			self.publicFilePath = (
				self.publicFolderPath +
				"client-" +
				self.id +
				".key")

			self.privateFilePath = (
				self.privateFolderPath +
				"client-" +
				self.id +
				".key_secret")

			self._generateCertificates()

			GlobalCertificateHandler.__instance = self
		else:
			return GlobalCertificateHandler.__instance

	@staticmethod
	def getInstance():
		if GlobalCertificateHandler.__instance is None:
			GlobalCertificateHandler()

		return GlobalCertificateHandler.__instance

	def _generateCertificates(self):
		if os.path.exists(self.basePath):
			shutil.rmtree(self.basePath)

		os.mkdir(self.basePath)
		os.mkdir(self.publicFolderPath)
		os.mkdir(self.privateFolderPath)

		public, private = zmq.auth.create_certificates(
			self.basePath, "client-" + self.id)

		shutil.move(public, self.publicFilePath)
		shutil.move(private, self.privateFilePath)

	# to be deprecated
	def getCertificatesPaths(self):
		return self.publicFolderPath, self.privateFolderPath

	def getCertificateFilePaths(self):
		return self.publicFilePath, self.privateFilePath

	def getCertificateFolderPaths(self):
		return self.privateFolderPath, self.privateFolderPath

	def getKeys(self):
		_, privatePath = self.getCertificateFilePaths()

		publicKey, privateKey = zmq.auth.load_certificate(privatePath)

		return publicKey, privateKey

	def getServerKeyFilePath(self):
		serverKeyPath = '../server-front.key'

		return serverKeyPath

	def storeServerKey(self, key):
		path = self.getServerKeyFilePath()

		fileContents = 'metadata\ncurve\n    public-key = "' + key + '"'

		print("FILE CONTENTS:\n", fileContents)

		with open(path, 'w') as fp:
			fp.write(fileContents)

	def cleanup():
		pass


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


class CertificateHandler():
	def __init__(self, id):
		self.id = id
		self.basePath = '../Certificates'

		self.publicFolderPath = (
			self.basePath +
			'/Public-' +
			str(id) +
			'/')

		self.privateFolderPath = (
			self.basePath +
			'/Private-' +
			str(id) +
			'/')

		self.publicFilePath = (
			self.publicFolderPath +
			"client-" +
			self.id +
			".key")

		self.privateFilePath = (
			self.privateFolderPath +
			"client-" +
			self.id +
			".key_secret")

		self._generateCertificates()

	def _generateCertificates(self):
		if os.path.exists(self.publicFolderPath):
				shutil.rmtree(self.publicFolderPath)

		if os.path.exists(self.privateFolderPath):
			shutil.rmtree(self.privateFolderPath)

		if not os.path.exists(self.basePath):
			os.mkdir(self.basePath)

		os.mkdir(self.publicFolderPath)
		os.mkdir(self.privateFolderPath)

		public, private = zmq.auth.create_certificates(
			self.basePath, "client-" + self.id)

		shutil.move(public, self.publicFilePath)
		shutil.move(private, self.privateFilePath)

	def getCertificatesPaths(self):
		return self.publicFolderPath, self.privateFolderPath

	def getServerKey(self):
		serverKeyPath = '../server-front.key'

		if os.path.exists(serverKeyPath):
			return serverKeyPath
		else:
			print("Error: Missing Certificates at", serverKeyPath)
			sys.exit()

	def cleanup(self):
		shutil.rmtree(self.publicFolderPath)
		shutil.rmtree(self.privateFolderPath)


class displayConnector(QObject):
		newFrameSignal = Signal(QPixmap)

		def __init__(self, display):
			QObject.__init__(self)
			self.newFrameSignal.connect(display.updateDisplay)

		def emitFrame(self, pmap):
			self.newFrameSignal.emit(pmap)


class Monitor(Thread):
	def __init__(self, socket, feedID):
		Thread.__init__(self)
		self.socket = socket
		self.feedID = feedID

		self.events = {
			"EVENT_CONNECTED": zmq.EVENT_CONNECTED,
			"EVENT_CONNECT_DELAYED": zmq.EVENT_CONNECT_DELAYED,
			"EVENT_CONNECT_RETRIED": zmq.EVENT_CONNECT_RETRIED,
			"EVENT_LISTENING": zmq.EVENT_LISTENING,
			"EVENT_BIND_FAILED": zmq.EVENT_BIND_FAILED,
			"EVENT_ACCEPTED": zmq.EVENT_ACCEPTED,
			"EVENT_ACCEPT_FAILED": zmq.EVENT_ACCEPT_FAILED,
			"EVENT_CLOSED": zmq.EVENT_CLOSED,
			"EVENT_CLOSE_FAILED": zmq.EVENT_CLOSE_FAILED,
			"EVENT_DISCONNECTED": zmq.EVENT_DISCONNECTED,
			"EVENT_ALL": zmq.EVENT_ALL,
			"EVENT_MONITOR_STOPPED": zmq.EVENT_MONITOR_STOPPED,
			"EVENT_HANDSHAKE_FAILED_NO_DETAIL": zmq.EVENT_HANDSHAKE_FAILED_NO_DETAIL,
			"EVENT_HANDSHAKE_SUCCEEDED": zmq.EVENT_HANDSHAKE_SUCCEEDED,
			"EVENT_HANDSHAKE_FAILED_PROTOCOL": zmq.EVENT_HANDSHAKE_FAILED_PROTOCOL,
			"EVENT_HANDSHAKE_FAILED_AUTH": zmq.EVENT_HANDSHAKE_FAILED_AUTH}

		# for key, val in self.events.items():
		# 	print(key, val)

	def run(self):
		while True:
			msg = recv_monitor_message(self.socket)

			event = msg.get("event")
			value = msg.get("value")
			endpoint = msg.get("endpoint")

			assigned = False
			for key, val in self.events.items():
				if event == val:
					assigned = True
					# print(key, endpoint)

			if assigned is False:
				print(msg)


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
		self.displayConn = displayConnector(display)
		self.mainDisplayConn = displayConnector(mainDisplay)
		self.mainDisplay = mainDisplay

	def setupSocket(self, feedID, addr, serverKey=None):
		if feedID == 'front':
			self.certHandler = GlobalCertificateHandler.getInstance()
			serverPath = self.certHandler.getServerKey()
			serverKey = zmq.auth.load_certificate(serverPath)[0]
		else:
			self.certHandler = CertificateHandler(feedID)

		publicPath, privatePath = self.certHandler.getCertificatesPaths()

		if feedID == 'front':
			self.ctxHandler = GlobalContextHandler.getInstance(publicPath)
		else:
			self.ctxHandler = ContextHandler(publicPath)

		context = self.ctxHandler.getContext()

		socket = context.socket(zmq.REQ)
		privateFile = privatePath + "client-" + feedID + ".key_secret"
		publicKey, privateKey = zmq.auth.load_certificate(privateFile)
		socket.curve_secretkey = privateKey
		socket.curve_publickey = publicKey

		if feedID == 'front':
			socket.curve_serverkey = serverKey
		else:
			socket.curve_serverkey = bytes(serverKey, 'utf-8')
		socket.connect(addr)

		return socket

	def initialize(self, feedID):
		socket = self.setupSocket('front', self.serverAddr + self.initPort)
		socket.send_string(feedID)
		initData = socket.recv_string()
		parts = initData.split(" ")

		mainPort = ':' + parts[0]
		serverKey = parts[1]

		return mainPort, serverKey

	def run(self):
		global mainFeedID
		feedID = str(self.camera.id).replace(' ', '')
		feedID = feedID.replace('/', '')
		feedID = feedID.replace('\\', '')
		feedID = feedID.replace(':', '')

		port, serverKey = self.initialize(feedID)

		socket = self.setupSocket(feedID, self.serverAddr + port, serverKey)
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
				if self.camera.id == self.mainDisplay.camera.id:
					self.mainDisplayConn.emitFrame(frames[1])

		socket.disable_monitor()
		socket.close()
		self.ctxHandler.cleanup()
		self.certHandler.cleanup()
		print("clean up finished")
