import base64 as b64
import cv2
import logging
from threading import Thread

import numpy as np
import zmq

from certificate_handler import CertificateHandler
from context_handler import ContextHandler
from feed_process_helper import FeedProcessHelper, BackgroundRemover
from modelHandler import ModelHandler
from monitor import Monitor
from results_handler import ResultsHandler
from terminator import Terminator
import _pickle as pickle


class FeedHandler(Thread):
	def __init__(self, feedID, clientKey):
		Thread.__init__(self)
		self.setName("FeedHandler")
		self.terminator = Terminator.getInstance()

		self.certHandler = CertificateHandler(feedID, 'server')
		self.certHandler.prep()

		self.publicKey, privateKey = self.certHandler.getKeyPair()
		clientsPath = self.certHandler.getEnrolledKeysPath()

		self.ctxHandler = ContextHandler(clientsPath)
		context = self.ctxHandler.getContext()

		self.saveClientKey(clientKey)

		self.socket = context.socket(zmq.REP)
		self.socket.setsockopt(zmq.RCVTIMEO, 20000)

		monitorSocket = self.socket.get_monitor_socket()
		self.monitor = Monitor(monitorSocket, feedID)
		self.monitor.setDaemon(True)
		self.monitor.start()

		self.socket.curve_secretkey = privateKey
		self.socket.curve_publickey = self.publicKey
		self.socket.curve_server = True

		self.port = self.socket.bind_to_random_port('tcp://*',
													min_port=49151,
													max_port=65535)
		self.feedID = feedID

	def getPort(self):
		return self.port

	def getPublicKey(self):
		return self.publicKey

	def saveClientKey(self, key):
		print('saving', key)
		self.certHandler.savePublicKey(key)
		print('cofiguring')
		self.ctxHandler.configureAuth()

	def run(self):
		helper = FeedProcessHelper()
		modelHandler = ModelHandler.getInstance()

		model = modelHandler.getModel()
		session = modelHandler.getSession()
		graph = modelHandler.getGraph()

		resultHandler = ResultsHandler(9, 30)

		bgRemover = BackgroundRemover()

		with session.as_default():
			with graph.as_default():
				while not self.terminator.isTerminating():
					try:
						received = self.socket.recv_string()
					except:
						break

					# handling timeout for deferred thread
					if received == 'wait':
						self.socket.send_string("ok")
						print('waiting')
					else:
						jpegStr = b64.b64decode(received)
						jpeg = np.fromstring(jpegStr, dtype=np.uint8)
						frame = cv2.imdecode(jpeg, 1)

						regions, drawCoords = helper.extractRegions(frame, 3, (64, 64), True)
						results = np.around(model.predict(regions)[:, 10:], decimals=3)
						resultHandler.append(results)
						finalResult = resultHandler.assess()

						boundingBoxes = bgRemover.apply(frame)

						response = pickle.dumps((finalResult, boundingBoxes), protocol=4)
						self.socket.send(response)

		# self.socket.disable_monitor()
		self.monitor.stop = True
		self.ctxHandler.cleanup()
		self.certHandler.cleanup()
		self.socket.close()
		print("Ending thread", self.feedID)
