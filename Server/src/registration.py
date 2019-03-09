import os
import threading
import time
import uuid
from threading import Thread
import zmq

# import MySQLdb as sql
from certificate_handler import CertificateHandler
from context_handler import ContextHandler
from terminator import Terminator
from monitor import Monitor


# db = sql.connect(
# 	os.environ["DBHOST"], os.environ["DBUSER"],
# 	os.environ["DBPASS"], os.environ["DBNAME"])

# cursor = db.cursor()

# count = None

# while count != 0:
# 	id = uuid.uuid4().hex
# 	cursor.execute("select * from productKey where activationKey = %s", (id,))
# 	count = cursor.rowcount

# cursor.execute("insert into productKey (activationKey) values (%s)", (id,))
# db.commit()

# print("Activation Key:", id)


class RegistrationListener(Thread):
	def __init__(self):
		Thread.__init__(self)
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

		print(publicKey)

		self.socket.bind('tcp://0.0.0.0:5001')
		self.socket.setsockopt(zmq.RCVTIMEO, 10000)

		monitorSocket = self.socket.get_monitor_socket()
		self.monitor = Monitor(monitorSocket, 'Registration')
		self.monitor.setDaemon(True)
		self.monitor.start()

		print("Listening on", 'tcp://0.0.0.0:5001')

	def run(self):
		while not self.terminator.isTerminating():
			try:
				received = self.socket.recv_string()
				print(received)
				parts = recevied.split(' ')

				if parts[0] == "REGISTER":
					
				elif parts[0] == "ACTIVATE":
					
				else:
					

				self.socket.send_string('True  No DB  1')
			except:
				pass

		self.monitor.stop = True
		self.socket.disable_monitor()
		self.socket.close()
		self.ctxHandler.cleanup()
		print("Ending Registration Listener Thread")

if __name__ == '__main__':
	terminator = Terminator.getInstance()

	regListener = RegistrationListener()
	regListener.setDaemon(True)
	regListener.start()

	while not terminator.isTerminating():
		time.sleep(1)
