import os
import threading
import time
import uuid
from threading import Thread
import zmq

from argon2 import PasswordHasher

# import MySQLdb as sql
from certificate_handler import CertificateHandler
from context_handler import ContextHandler
from terminator import Terminator
from monitor import Monitor

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
					success = True
					msg = 'Account Registered'

					hasher = PasswordHasher()

					try:
						username = parts[1]
						password = hasher.hash(parts[2])
						email = parts[3]
					except:
						success = False
						msg += '\n\tError in parameters provided'

					if success:
						global cursor

						cursor.execute(
							"""select * from users where username = %s""", (username,))

						if cursor.rowcount != 0:
							success = False
							msg += '\n\tUsername already taken'

						cursor.execute(
							"""select * from users where username = %s""", (email, ))

						if cursor.rowcount != 0:
							success = False
							msg += '\n\tEmail already registered'

						if success:
							count = cursor.execute(
								"""insert into users(username, password, email)
								values(%s, %s, %s)""", (username, password, email))
							userID = cursor.lastrowid

							cursor.commit()

							if count == 1 and userID is not None:
								found = None

								while found != 0:
									key = uuid.uuid4().hex
									cursor.execute(
										"""select * from productKey where activationKey = %s""",
										(key,))

									found = cursor.rowcount

								inserted = cursor.execute(
									"""insert into productKey(activationKey, userID)
									values(%s, %s)""", (key, userID))

								cursor.commit()

								if inserted != 1:
									success = False
									msg = 'Failed to register activation key, contact support.'
							else:
								success = False
								msg += '\n\tFailed to register'

				elif parts[0] == "ACTIVATE":
					success = True
					msg = 'Account Activated'

					try:
						key = parts[1]
						userID = parts[2]
					except:
						success = False
						msg = 'Error in parameters provided'

					if success:
						cursor.execute(
							"""select * from productKey
							where activationKey = %s and userID = %s""", (key, userID))

						if cursor.rowcount != 1:
							success = False
							msg = 'Key not registered to user.'
						else:
							cursor.execute(
								"""update productKey
								set activationCount = activationCount + 1
								where activationKey = %s and userID = %s""", (key, userID))
				else:	
					success = False
					msg = 'Invalid Instruction'

				self.socket.send_string(str(success) + '  ' + msg + '  ' + str(usedID))
			except:
				pass

		self.monitor.stop = True
		self.socket.disable_monitor()
		self.socket.close()
		self.ctxHandler.cleanup()
		print("Ending Registration Listener Thread")

if __name__ == '__main__':
	terminator = Terminator.getInstance()

	db = sql.connect(
 	os.environ["DBHOST"], os.environ["DBUSER"],
 	os.environ["DBPASS"], os.environ["DBNAME"])

	cursor = db.cursor()

	regListener = RegistrationListener()
	regListener.setDaemon(True)
	regListener.start()

	while not terminator.isTerminating():
		time.sleep(1)
