from threading import Thread
import zmq
from terminator import Terminator
from certificate_handler import CertificateHandler
import logging


class Enroller(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.setName("Enroller")

		self.terminator = Terminator.getInstance()
		self.unsecuredCtx = zmq.Context()
		self.unsecuredSocket = self.unsecuredCtx.socket(zmq.REP)
		self.unsecuredSocket.bind('tcp://0.0.0.0:5002')
		self.unsecuredSocket.setsockopt(zmq.RCVTIMEO, 10000)

		self.certHandler = CertificateHandler(id="front")
		self.publicKey, _ = self.certHandler.getKeys()

		def run(self):
			while not self.terminator.isTerminating():
				try:
					clientKey = self.unsecuredSocket.recv_string()
					self.certHandler.saveClientKey(clientKey)

					self.unsecuredSocket.send_string(str(self.publicKey))

					logging.debug("New client enrolled %s", clientKey)
				except:
					pass

			self.unsecuredSocket.close()
