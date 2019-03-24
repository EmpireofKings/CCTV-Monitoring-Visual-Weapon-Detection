# TODO

import logging
import os
import string
import sys
import threading
import time 
import cv2

import zmq
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtMultimedia import *
from pprint import pprint

# Appending CommonFiles to system path for importing
# relatively messy but not many options to do this.
path = os.getcwd().split('\\')
path = '\\'.join(path[:len(path) - 2])
sys.path.append(path + '\\CommonFiles')

from config_gui import Config
from data_handler import *
from deferred_gui import DeferredAnalysis
from live_gui import LiveAnalysis
from validator import Validator
from context_handler import ContextHandler
from certificate_handler import CertificateHandler
from terminator import Terminator
from corner_controls import CornerControls

serverAddr = 'tcp://35.204.135.105'
localAddr = 'tcp://127.0.0.1'
mainAddr = localAddr
connectCamPort = ':5000'
registrationPort = ':5001'
unsecuredEnrollPort = ':5002'

userConfig = '../userDetails.config'


class mainWindow(QMainWindow):
	def __init__(self, app):
		QMainWindow.__init__(self)

		self.app = app
		authenticated = False

		self.terminator = Terminator.getInstance()

		if os.path.exists(userConfig):
			logging.debug('Authenticating on saved user details')
			authenticated, msg = self.authenticateUserDetails()

		if not authenticated:
			logging.debug('Not already logged in, presenting dialog.')
			loginDialog = LoginDialog()
			authenticated, msg, userID, key = loginDialog.getUserData()

			self.saveUserDetails(userID, key)

		if authenticated:
			logging.debug('User authenticated, initialising tabs.')
			tabs = MainWindowTabs(app)
			self.setCentralWidget(tabs)
		else:
			self.closeEvent(None)

	def saveUserDetails(self, userID, key):
		with open(userConfig, 'w') as fp:
			fileContents = str(userID) + '\t' + str(key)
			fp.write(fileContents)

	def authenticateUserDetails(self):
		authenticated = False
		msg = ''

		try:
			with open(userConfig, 'r') as fp:
				data = fp.read()
				parts = data.split('\t')
				userID = parts[0]
				key = parts[1]

			socket = setupGlobalSocket(mainAddr + registrationPort)
			socket.send_string('AUTHENTICATE' + ' ' + userID + ' ' + key)
			result = socket.recv_string()
			print("RAW RESULT", result)
			parts = result.split('  ')

			if parts[0] == 'True':
				authenticated = True
				msg = 'Authenticated by userID and key'
			else:
				authenticated = False
				msg = 'Failed to authenticate'
		except:
			authenticated = False
			msg = 'Failed to authenticate'
			os.remove(userConfig)

		return authenticated, msg

	def closeEvent(self, event):
		self.terminator.autoTerminate()

		threads = threading.enumerate()

		for thread in threads:
			thread.join()

		shutil.rmtree('../data/Sounds')
		self.app.exit()
		sys.exit()

class LoginDialog(QDialog):
	def __init__(self):
		QDialog.__init__(
			self, None,
			Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

		tabs = QTabWidget()
		tabs.addTab(self.setupLoginTab(), "Login")
		tabs.addTab(self.setupRegisterTab(), "Register")

		outerLayout = QHBoxLayout()
		outerLayout.addWidget(tabs)
		self.setLayout(outerLayout)

	def setupLoginTab(self):
		loginTab = QWidget()

		usernameLayout = QHBoxLayout()
		usernameLabel = QLabel("Username: ")
		self.usernameEntryLogin = QLineEdit()
		self.usernameEntryLogin.setAlignment(Qt.AlignRight)
		self.usernameEntryLogin.setFixedWidth(150)
		usernameLayout.addWidget(usernameLabel)
		usernameLayout.addWidget(self.usernameEntryLogin)

		passwordLayout = QHBoxLayout()
		passwordLabel = QLabel("Password: ")
		self.passwordEntryLogin = QLineEdit()
		self.passwordEntryLogin.setEchoMode(QLineEdit.Password)
		self.passwordEntryLogin.setAlignment(Qt.AlignRight)
		self.passwordEntryLogin.setFixedWidth(150)
		passwordLayout.addWidget(passwordLabel)
		passwordLayout.addWidget(self.passwordEntryLogin)

		buttonLayout = QHBoxLayout()
		loginButton = QPushButton("Login")
		loginButton.clicked.connect(self.login)
		exitButton = QPushButton("Exit")
		exitButton.clicked.connect(self.exit)
		buttonLayout.addWidget(loginButton)
		buttonLayout.addWidget(exitButton)

		self.msgLabelLogin = QLabel()

		outerLoginLayout = QVBoxLayout()
		outerLoginLayout.addLayout(usernameLayout)
		outerLoginLayout.addLayout(passwordLayout)
		outerLoginLayout.addLayout(buttonLayout)
		outerLoginLayout.addWidget(self.msgLabelLogin)
		loginTab.setLayout(outerLoginLayout)

		return loginTab

	def setupRegisterTab(self):
		registerTab = QWidget()

		usernameLayout = QHBoxLayout()
		usernameLabel = QLabel("Username:")
		self.usernameEntryRegister = QLineEdit()
		self.usernameEntryRegister.setMaxLength(32)
		self.usernameEntryRegister.setAlignment(Qt.AlignRight)
		self.usernameEntryRegister.setFixedWidth(150)
		usernameLayout.addWidget(usernameLabel)
		usernameLayout.addWidget(self.usernameEntryRegister)

		emailLayout = QHBoxLayout()
		emailLabel = QLabel("Email:")
		self.emailEntryRegister = QLineEdit()
		self.emailEntryRegister.setMaxLength(254)
		self.emailEntryRegister.setAlignment(Qt.AlignRight)
		self.emailEntryRegister.setFixedWidth(150)
		emailLayout.addWidget(emailLabel)
		emailLayout.addWidget(self.emailEntryRegister)

		passwordLayout = QHBoxLayout()
		passwordLabel = QLabel("Password:")
		self.passwordEntryRegister = QLineEdit()
		self.passwordEntryRegister.setEchoMode(QLineEdit.Password)
		self.passwordEntryRegister.setMaxLength(128)
		self.passwordEntryRegister.setAlignment(Qt.AlignRight)
		self.passwordEntryRegister.setFixedWidth(150)
		passwordLayout.addWidget(passwordLabel)
		passwordLayout.addWidget(self.passwordEntryRegister)

		passConfLayout = QHBoxLayout()
		passConfLabel = QLabel("Confirm Password:")
		self.passConfEntryRegister = QLineEdit()
		self.passConfEntryRegister.setEchoMode(QLineEdit.Password)
		self.passConfEntryRegister.setMaxLength(128)
		self.passConfEntryRegister.setAlignment(Qt.AlignRight)
		self.passConfEntryRegister.setFixedWidth(150)
		passConfLayout.addWidget(passConfLabel)
		passConfLayout.addWidget(self.passConfEntryRegister)

		buttonLayout = QHBoxLayout()
		registerButton = QPushButton("Register")
		registerButton.clicked.connect(self.register)
		exitButton = QPushButton("Exit")
		exitButton.clicked.connect(self.exit)
		buttonLayout.addWidget(registerButton)
		buttonLayout.addWidget(exitButton)

		self.msgLabelRegister = QLabel()

		outerRegisterLayout = QVBoxLayout()
		outerRegisterLayout.addLayout(usernameLayout)
		outerRegisterLayout.addLayout(emailLayout)
		outerRegisterLayout.addLayout(passwordLayout)
		outerRegisterLayout.addLayout(passConfLayout)
		outerRegisterLayout.addLayout(buttonLayout)
		outerRegisterLayout.addWidget(self.msgLabelRegister)
		registerTab.setLayout(outerRegisterLayout)

		return registerTab

	def login(self):
		username = self.usernameEntryLogin.text()
		password = self.passwordEntryLogin.text()

		self.authenticated, self.msg, self.userID, self.key = self.verifyUser(username, password)
		print(self.msg)
		if self.authenticated:
			self.accept()
		else:
			self.msgLabelLogin.setText(self.msg)

	def verifyUser(self, username, password):
		authenticated = False
		msg = ''

		socket = setupGlobalSocket(mainAddr + registrationPort)
		socket.send_string('LOGIN' + ' ' + username + ' ' + password)
		result = socket.recv_string()
		parts = result.split('  ')

		if parts[0] == 'True':
			authenticated = True
		else:
			authenticated = False

		return authenticated, parts[1], parts[2], parts[3]

	def register(self):
		username = self.usernameEntryRegister.text()
		password = self.passwordEntryRegister.text()
		passConf = self.passConfEntryRegister.text()
		email = self.emailEntryRegister.text()

		validParameters = True
		msg = ''

		validator = Validator()

		validUsername, usernameMsg = validator.validateUsername(username)
		if usernameMsg != '':
			msg += '\nUsername:' + usernameMsg

		# password validation uses username
		if validUsername:
			validPassword, passwordMsg = validator.validatePassword(
				password, passConf, username)

			if passwordMsg != '':
				msg += '\nPassword:' + passwordMsg

		validEmail, emailMsg = validator.validateEmail(email)
		if emailMsg != '':
			msg += '\nEmail:' + emailMsg

		if validUsername and validPassword and validEmail:
			data = self.registerUser(
				username,
				password,
				email)

			registered = data[0]
			msg = data[1]
			self.userID = data[2]

			if registered:
				activationDialog = ActivationDialog()
				activationDialog.setWindowTitle("Activation")
				self.authenticated, self.msg, self.key = activationDialog.getKey(self.userID)
				if self.authenticated:
					self.accept()
				else:
					self.msgLabelRegister.setText('Error please try again')
			else:
				self.msgLabelRegister.setText(msg)
		else:
			self.msgLabelRegister.setText(msg)

	def registerUser(self, username, password, email):
		print("register user")
		socket = setupGlobalSocket(mainAddr + registrationPort)
		socket.send_string('REGISTER ' + username + ' ' + password + ' ' + email)
		print("sent")
		result = socket.recv_string()
		print(result)
		socket.close()

		parts = result.split('  ')
		result = parts[0]
		msg = parts[1]
		userID = parts[2]

		if result == 'True':
			return True, msg, userID
		else:
			return False, msg, userID

	def exit(self):
		sys.exit()

	def getUserData(self):
		self.exec()
		return self.authenticated, self.msg, self.userID, self.key

	def closeEvent(self, event):
		sys.exit()


class ActivationDialog(QDialog):
	def __init__(self):
		QDialog.__init__(self)

		outerLayout = QVBoxLayout()
		activationLayout = QHBoxLayout()
		activationLabel = QLabel("Activation Key: ")
		self.activationEntryRegister = QLineEdit()
		self.activationEntryRegister.setMaxLength(32)
		activationLayout.addWidget(activationLabel)
		activationLayout.addWidget(self.activationEntryRegister)

		buttonLayout = QHBoxLayout()
		registerButton = QPushButton("Activate")
		registerButton.clicked.connect(self.activate)
		exitButton = QPushButton("Cancel")
		exitButton.clicked.connect(self.cancel)
		buttonLayout.addWidget(registerButton)
		buttonLayout.addWidget(exitButton)

		self.msgLabelActivate = QLabel()

		outerLayout.addLayout(activationLayout)
		outerLayout.addLayout(buttonLayout)
		outerLayout.addWidget(self.msgLabelActivate)
		self.setLayout(outerLayout)

	def activate(self):
		self.key = self.activationEntryRegister.text()
		validator = Validator()
		validKey, self.msg = validator.validateKey(self.key)

		if validKey:
			socket = setupGlobalSocket(mainAddr + registrationPort)
			socket.send_string('ACTIVATE ' + self.key + ' ' + self.userID)
			result = socket.recv_string()
			parts = result.split('  ')

			activated = parts[0]
			self.msg = parts[1]

			if activated == 'True':
				self.authenticated = True
			else:
				self.authenticated = False

			if self.authenticated:
				self.accept()
			else:
				self.msgLabelActivate.setText(self.msg)
		else:
			self.msgLabelActivate.setText(self.msg)

	def cancel(self):
		self.reject()

	def getKey(self, userID):
		self.userID = userID
		self.exec()
		return self.authenticated, self.msg, self.key


def setupGlobalSocket(addr):
	certHandler = CertificateHandler('front', 'client')
	serverKey = certHandler.getEnrolledKeys()
	publicKey, privateKey = certHandler.getKeyPair()

	ctxHandler = ContextHandler(certHandler.getEnrolledKeysPath())
	context = ctxHandler.getContext()

	socket = context.socket(zmq.REQ)
	socket.curve_secretkey = privateKey
	socket.curve_publickey = publicKey
	socket.curve_serverkey = serverKey

	socket.connect(mainAddr + registrationPort)

	return socket


class MainWindowTabs(QTabWidget):
	def __init__(self, app):
		QTabWidget.__init__(self)

		dataLoader = DataLoader()

		try:
			self.configTab = Config(app, dataLoader)
			self.liveTab = LiveAnalysis(app, dataLoader)
			self.deferredTab = DeferredAnalysis(app)
			self.cornerWidget = CornerControls(app)
			logging.debug('Tabs initialised')
		except:
			logging.critical('Tabs failed to initialise', exc_info=True)

		# Icons acquired from www.flaticon.com licensed by
		# Creative Commons BY 3.0 http://creativecommons.org/licenses/by/3.0/

		# Icon made by Fermam Aziz  https://www.flaticon.com/authors/fermam-aziz
		configIcon = QIcon("../data/icons/config.png")

		# Icon made by photo3idea_studio
		# https://www.flaticon.com/authors/photo3idea-studio
		liveIcon = QIcon("../data/icons/live.png")

		# Icon made by Smashicons https://www.flaticon.com/authors/smashicons
		deferredIcon = QIcon("../data/icons/deferred.png")

		self.addTab(self.liveTab, liveIcon, "Live Analysis")
		self.addTab(self.deferredTab, deferredIcon, "Deferred Analysis")
		self.addTab(self.configTab, configIcon, "Configuration")
		self.setCornerWidget(self.cornerWidget)

		self.currentChanged.connect(self.tabChanged)

	def tabChanged(self, index):
		if index == 0:
			logging.debug('Live tab focused')
		elif index == 1:
			logging.debug('Deferred tab focused')
		elif index == 2:
			logging.debug('Config tab focused')
		else:
			logging.error('Error interpreting tab index')


def enroll():
	try:
		unsecuredCtx = zmq.Context()
		unsecuredSocket = unsecuredCtx.socket(zmq.REQ)
		unsecuredSocket.setsockopt(zmq.RCVTIMEO, 5000)
		unsecuredSocket.setsockopt(zmq.SNDTIMEO, 5000)
		unsecuredSocket.setsockopt( zmq.LINGER, 0 )

		unsecuredSocket.connect(mainAddr + unsecuredEnrollPort)
		certHandler = CertificateHandler('front', 'client')
		certHandler.prep()
		publicKey, _ = certHandler.getKeyPair()

		publicKey = publicKey.decode('utf-8')

		unsecuredSocket.send_string(str(publicKey))
		serverKey = unsecuredSocket.recv_string()	

		certHandler.savePublicKey(serverKey)
		logging.debug('Enrolled')

	except Exception as e:
		logging.critical("Could not enroll", exc_info=True)
		unsecuredSocket.close()
		return False
	return True

		

if __name__ == '__main__':
	if len(sys.argv) == 2:
			mode = sys.argv[1]
			if mode == 'debug':
				loggerMode = logging.DEBUG
			elif mode == 'info':
				loggerMode = logging.INFO
			elif mode == 'warning':
				loggerMode = logging.WARNING
			elif mode == 'error':
				loggerMode = logging.ERROR
			elif mode == 'critical':
				loggerMode = logging.CRITICAL
	else:
		loggerMode = logging.INFO

	logging.basicConfig(
		format='%(levelname)s - %(asctime)s - %(threadName)s - %(message)s',
		level=loggerMode,
		handlers=
			[logging.FileHandler('../Logs/server_logs.txt'),
			logging.StreamHandler(sys.stdout)])

	logging.info('\n\n\n\t\tBegin new set of logs:\n\n\n')

	# certHandler = CertificateHandler('front', 'client')
	# certHandler.prep()
	app = QApplication(sys.argv)
	app.setApplicationName("CCTV Surveillance")

	enrolled = enroll()

	if enrolled:
		logging.debug('Enrollment Successful, starting main application')
		mainWindow = mainWindow(app)
		mainWindow.showMaximized()
	else:
		logging.error('Enrollment Failed')
		msgBox = QMessageBox()
		msgBox.setText("Could not enroll with server.\nCheck connection and try again.")
		msgBox.show()

	sys.exit(app.exec_())
