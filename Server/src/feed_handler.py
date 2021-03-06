# Ben Ryan C15507277

import base64 as b64
import logging
from threading import Thread

import cv2
import numpy as np
import zmq

import _pickle as pickle
from certificate_handler import CertificateHandler
from context_handler import ContextHandler
from feed_process_helper import BackgroundRemover, FeedProcessHelper
from modelHandler import ModelHandler
from monitor import Monitor
from results_handler import ResultsHandler
from terminator import Terminator


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
		self.certHandler.savePublicKey(key)
		self.ctxHandler.configureAuth()

	def run(self):
		helper = FeedProcessHelper()
		modelHandler = ModelHandler.getInstance()

		model = modelHandler.getModel()
		session = modelHandler.getSession()
		graph = modelHandler.getGraph()

		resultHandler = ResultsHandler(16, 5)

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
					else:
						jpegStr = b64.b64decode(received)
						jpeg = np.fromstring(jpegStr, dtype=np.uint8)
						frame = cv2.imdecode(jpeg, 1)
						height, width, _ = np.shape(frame)

						regions, drawCoords = helper.extractRegions(frame, 4, (64, 64))
						results = np.around(model.predict(regions)[:, 10:], decimals=3)
						resultHandler.append(results)
						finalResult, bboxIndex = resultHandler.assess()

						boundingBoxes = bgRemover.apply(frame)

						response = pickle.dumps(
							(finalResult, boundingBoxes,
							(resultHandler.getAverages(), drawCoords)), protocol=4)
						self.socket.send(response)

		# self.socket.disable_monitor()
		self.monitor.stop = True
		self.ctxHandler.cleanup()
		self.certHandler.cleanup()
		self.socket.close()
		logging.debug("Ending thread %s", self.feedID)


def scale(val, inMin, inMax, outMin, outMax):
	return ((val - inMin) / (inMax - inMin)) * (outMax - outMin) + outMin
