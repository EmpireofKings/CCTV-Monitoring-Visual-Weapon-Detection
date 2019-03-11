from terminator import Terminator
from certificate_handler import CertificateHandler
from context_handler import ContextHandler
import zmq
from feed_handler import FeedHandler
from threading import Thread
import logging


class FeedListener(Thread):
	def __init__(self, addr):
		Thread.__init__(self)
		self.setName("FeedListener")
		self.terminator = Terminator.getInstance()
		certHandler = CertificateHandler(id="front")
		publicPath, privatePath = certHandler.getCertificatesPaths()

		self.ctxHandler = ContextHandler(publicPath)
		context = self.ctxHandler.getContext()
		self.socket = context.socket(zmq.REP)

		privateFile = privatePath + "server-front.key_secret"
		publicKey, privateKey = zmq.auth.load_certificate(privateFile)
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

				print("New connection from ", received)
				handler = FeedHandler(received)
				handler.setDaemon(True)
				handler.start()

				assignedPort = handler.getPort()
				publicKey = handler.getPublicKey()

				self.socket.send_string(str(assignedPort) + " " + str(publicKey, 'utf-8'))
			except:
				pass

		self.socket.close()
		self.ctxHandler.cleanup()
		logging.info('Feed listener thread shutting down')
