# Ben Ryan C15507277

import logging
import threading
from threading import Thread

import zmq

from certificate_handler import CertificateHandler
from monitor import Monitor
from terminator import Terminator


class Enroller(Thread):
	def __init__(self, feedListener, authListener):
		Thread.__init__(self)
		self.setName("Enroller")

		self.feedListener = feedListener
		self.authListener = authListener

		self.terminator = Terminator.getInstance()

		self.unsecuredCtx = zmq.Context()
		self.unsecuredSocket = self.unsecuredCtx.socket(zmq.REP)

		monitorSocket = self.unsecuredSocket.get_monitor_socket()
		self.monitor = Monitor(monitorSocket, "Enroller")
		self.monitor.setDaemon(True)
		self.monitor.start()

		self.unsecuredSocket.bind('tcp://0.0.0.0:5002')
		self.unsecuredSocket.setsockopt(zmq.RCVTIMEO, 10000)

		self.certHandler = CertificateHandler('front', 'server')
		self.publicKey, _ = self.certHandler.getKeyPair()

		self.publicKey = self.publicKey.decode('utf-8')

	def run(self):
		while not self.terminator.isTerminating():
			try:
				clientKey = self.unsecuredSocket.recv_string()
				self.certHandler.savePublicKey(clientKey)
				self.feedListener.ctxHandler.configureAuth()
				self.authListener.ctxHandler.configureAuth()
				self.unsecuredSocket.send_string(str(self.publicKey))
				logging.debug("New client enrolled %s", clientKey)
			except:
				logging.debug('Error enrolling')

		self.unsecuredSocket.close()
		self.monitor.stop = True
		logging.info('Enroller thread shutting down')
