from threading import Thread
import zmq
from terminator import Terminator
from certificate_handler import CertificateHandler
import logging
from monitor import Monitor
import threading


class Enroller(Thread):
	def __init__(self, feedListener, authListener):
		Thread.__init__(self)
		self.setName("Enroller")

		self.feedListener = feedListener
		self.authListener = authListener

		self.terminator = Terminator.getInstance()

		self.unsecuredCtx = zmq.Context()
		self.unsecuredSocket = self.unsecuredCtx.socket(zmq.REP)
		self.unsecuredSocket.bind('tcp://0.0.0.0:5002')
		self.unsecuredSocket.setsockopt(zmq.RCVTIMEO, 10000)

		monitorSocket = self.unsecuredSocket.get_monitor_socket()
		monitor = Monitor(monitorSocket, "Enroller")
		monitor.setDaemon(True)
		monitor.start()

		self.certHandler = CertificateHandler(id="front")
		self.publicKey, _ = self.certHandler.getKeys()

		self.publicKey = self.publicKey.decode('utf-8')

	def run(self):
		while not self.terminator.isTerminating():
			try:
				clientKey = self.unsecuredSocket.recv_string()
				print("RECEVIED", clientKey)
				self.certHandler.saveClientKey(clientKey)
				print("SAVED")
				self.feedListener.ctxHandler.configureAuth()
				self.authListener.ctxHandler.configureAuth()
				print("CONFIGURED")
				self.unsecuredSocket.send_string(str(self.publicKey))
				logging.debug("New client enrolled %s", clientKey)
			except:
				pass
		self.unsecuredSocket.close()
		logging.info('Enroller thread shutting down')
