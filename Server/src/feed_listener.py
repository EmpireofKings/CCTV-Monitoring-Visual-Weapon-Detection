import logging
from threading import Thread

import zmq

from certificate_handler import CertificateHandler
from context_handler import ContextHandler
from feed_handler import FeedHandler
from terminator import Terminator
from monitor import Monitor


class FeedListener(Thread):
	def __init__(self, addr):
		Thread.__init__(self)
		self.setName("FeedListener")
		self.terminator = Terminator.getInstance()

		certHandler = CertificateHandler("front", 'server')

		publicKey, privateKey = certHandler.getKeyPair()
		clientsPath = certHandler.getEnrolledKeysPath()

		self.ctxHandler = ContextHandler(clientsPath)
		context = self.ctxHandler.getContext()
		self.socket = context.socket(zmq.REP)

		monitorSocket = self.socket.get_monitor_socket()
		monitor = Monitor(monitorSocket, 'front')
		monitor.setDaemon(True)
		monitor.start()

		self.socket.curve_secretkey = privateKey
		self.socket.curve_publickey = publicKey
		self.socket.curve_server = True

		self.socket.bind(addr)
		self.socket.setsockopt(zmq.RCVTIMEO, 10000)
		logging.info('Socket setup, public key: %s', publicKey)

	def run(self):
		while not self.terminator.isTerminating():
			try:
				received = self.socket.recv_string()

				parts = received.split('  ')
				feedID = parts[0]
				clientKey = parts[1]

				logging.debug('Client key received %s for %s', clientKey, feedID)

				try:
					handler = FeedHandler(feedID, clientKey)
					handler.setDaemon(True)
					handler.start()

					logging.debug('Feed Handler thread started')
				except:
					logging.critical('Feed Handler thread failed to start', exc_info=True)

				assignedPort = handler.getPort()
				publicKey = handler.getPublicKey()

				self.socket.send_string(str(assignedPort) + '  ' + str(publicKey, 'utf-8'))
			except:
				pass

		self.socket.close()
		self.ctxHandler.cleanup()
		logging.info('Feed listener thread shutting down')
