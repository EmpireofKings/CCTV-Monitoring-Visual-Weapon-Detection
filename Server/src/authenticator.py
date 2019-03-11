import logging
import os
import smtplib
import threading
import time
import uuid
from email.message import EmailMessage
from threading import Thread

import zmq
from argon2 import PasswordHasher

import MySQLdb as sql
from certificate_handler import CertificateHandler
from context_handler import ContextHandler
from monitor import Monitor
from terminator import Terminator


class AuthenticationListener(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.terminator = Terminator.getInstance()
		self.setName("Authenticator")
		try:
			self.db = sql.connect(
				os.environ["DBHOST"], os.environ["DBUSER"],
				os.environ["DBPASS"], os.environ["DBNAME"])

			self.cursor = self.db.cursor()

			logging.debug('Connected to database')
		except:
			logging.critical('Exception occured connecting to database', exc_info=True)
			self.terminator.autoTerminate()

		try:
			certHandler = CertificateHandler(id="front")
			publicPath, privatePath = certHandler.getCertificatesPaths()
			clientKeysPath = certHandler.getClientKeysPath()

			self.ctxHandler = ContextHandler(clientKeysPath)
			context = self.ctxHandler.getContext()
			self.socket = context.socket(zmq.REP)

			privateFile = privatePath + "server-front.key_secret"
			publicKey, privateKey = zmq.auth.load_certificate(privateFile)
			self.socket.curve_secretkey = privateKey
			self.socket.curve_publickey = publicKey
			self.socket.curve_server = True
			self.socket.setsockopt(zmq.RCVTIMEO, 10000)
			self.socket.bind('tcp://0.0.0.0:5001')

			logging.debug('Socket setup and bound, listening')
		except:
			logging.critical('Exception occured setting up auth socket', exc_info=True)

		try:
			monitorSocket = self.socket.get_monitor_socket()
			self.monitor = Monitor(monitorSocket, 'Registration')
			self.monitor.setDaemon(True)
			self.monitor.start()

			logging.debug('Socket monitor thread started')
		except:
			logging.critical(
				'Exception occured starting socket monitor thread',
				exc_info=True)

	def run(self):
		while not self.terminator.isTerminating():
			try:
				data = self.socket.recv_string()
				received = True
			except:
				received = False
				pass

			if received:
				parts = data.split(' ')

				if parts[0] == "REGISTER":
					try:
						success, msg, userID = self.register(parts[1], parts[2], parts[3])
						self.socket.send_string(str(success) + '  ' + msg + '  ' + str(userID))
						logging.debug(
							'Responded to register instruction: %s, %s, %s',
							success, msg, userID)
					except:
						logging.error('Exception occured when registering', exc_info=True)

				elif parts[0] == "ACTIVATE":
					try:
						success, msg = self.activate(parts[1], parts[2])
						self.socket.send_string(str(success) + '  ' + msg)
						logging.debug(
							'Responded to activation instruction: %s, %s',
							success, msg)
					except:
						logging.error('Exception occured when activating', exc_info=True)

				elif parts[0] == 'LOGIN':
					try:
						success, msg, userID, key = self.login(parts[1], parts[2])
						self.socket.send_string(str(success) + '  ' + msg + '  ' + str(userID) + '  ' + str(key))
						logging.debug(
							'Responded to login instruction: %s, %s, %s, %s',
							success, msg, userID, key)
					except:
						logging.error('Exception occured when logging in', exc_info=True)

				elif parts[0] == 'AUTHENICATE':
					try:
						success, msg = self.authenticate(parts[1], parts[2])
						self.socket.send_string(str(success) + '  ' + msg)
						logging.debug(
							'Responded to authenticate instruction: %s, %s',
							success, msg)
					except:
						logging.error('Exception occured when authenticating', exc_info=True)

				else:
					try:
						success, msg = False, 'Invalid Instruction'
						self.socket.send_string(str(success) + '  ' + msg)
						logging.debug(
							'Responded to invalid instruction: %s, %s',
							success, msg)
					except:
						logging.error(
							'Exception occured when repsonding to invalid instruction',
							exc_info=True)

		try:
			self.monitor.stop = True
			self.socket.disable_monitor()
			self.socket.close()
			self.ctxHandler.cleanup()
			logging.debug('Authentication thread shutting down gracefully')
		except:
			logging.error(
				'Exception occured while cleaning up authentication thread for shutdown',
				exc_info=True)

	def register(self, username, password, email):
		success = False
		msg = ''
		userID = 'N/A'
		hasher = PasswordHasher()
		password = hasher.hash(password)
		cont = True

		self.cursor.execute(
			"""select * from users where username = %s""", (username,))

		if self.cursor.rowcount != 0:
			cont = False
			success = False
			msg += '\n\tUsername already taken'
			logging.debug('Username already taken: %s', username)

		self.cursor.execute(
			"""select * from users where email = %s""", (email, ))

		if self.cursor.rowcount != 0:
			cont = False
			success = False
			msg += '\n\tEmail already registered'
			logging.debug('Email already registered: %s', email)

		if cont:
			count = self.cursor.execute(
				"""insert into users(username, password, email)
				values(%s, %s, %s)""", (username, password, email))

			userID = self.cursor.lastrowid

			if count == 1 and userID is not None:
				found = None

				while found != 0:
					key = uuid.uuid4().hex
					self.cursor.execute(
						"""select * from productKey where activationKey = %s""",
						(key,))

					found = self.cursor.rowcount

				inserted = self.cursor.execute(
					"""insert into productKey(activationKey, userID)
					values(%s, %s)""", (key, userID))

				if inserted != 1:
					success = False
					msg += 'Failed to register activation key'
					self.db.rollback()
				else:

					self.db.commit()
					message = EmailMessage()
					message.set_content(key)
					message['Subject'] = 'Activation Key'
					message['From'] = 'ben96ryan@gmail.com'
					message['To'] = email

					try:
						mailserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
						mailserver.ehlo()
						mailserver.login(os.environ['EMAILUSER'], os.environ["EMAILPASS"])
						mailserver.send_message(message)
						mailserver.close()

						success = True
						msg += '\n\tSuccessfully Registered, check email for activation key.'
					except:
						logging.error('Exception occure emailing activation key', exc_info=True)
			else:
				success = False
				msg += '\n\tFailed to register'

		return success, msg, userID

	def activate(self, key, userID):
		success = False
		msg = ''

		self.cursor.execute(
			"""select * from productKey
			where activationKey = %s and id = %s""", (key, userID))

		if self.cursor.rowcount != 1:
			success = False
			msg += '\n\tKey not registered to user.'
		else:
			self.cursor.execute(
				"""update productKey
				set activationCount = activationCount + 1
				where activationKey = %s and id = %s""", (key, userID))
			self.db.commit()
			success = True
			msg = 'Successfully Activated'

		return success, msg

	def login(self, username, password):
		success = False
		msg = ''
		userID = 'N/A'
		key = 'N/A'

		self.cursor.execute(
			"""select password, id from users
			where username = %s""", (username,))

		if self.cursor.rowcount == 0:
			success = False
			msg += '\n\tUsername does not exists'

		elif self.cursor.rowcount != 1:
			success = False
			msg += '\n\tUnknown Error'

		else:
			row = self.cursor.fetchone()
			hashed = row[0]
			userID = row[1]

			verifier = PasswordHasher()
			try:
				verifier.verify(hashed, password)
				success = True
			except:
				success = False

			if success:
				msg += 'Authenticated'

				if verifier.check_needs_rehash(hashed):
					hashed = verifier.hash(password)
					count = self.cursor.execute(
						"""update users
						set password = %s
						where username = %s""",
						(hashed, username))

					if count != 1:
						msg += 'Failed to rehash password, contact support'
						logging.error('Failed to rehash password')
						self.db.rollback()
					else:
						self.db.commit()

				self.cursor.execute(
					"""select activationKey from productKey
					where userID = %s""", (userID,))

				row = self.cursor.fetchone()
				key = row[0]

			else:
				success = False
				msg += 'Incorrect Password'

		return success, msg, userID, key

	def authenticate(self):
		return True, '', 'N/A'
