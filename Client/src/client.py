# TODO

import os
import sys
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import threading

from live_gui import LiveAnalysis
from deferred_gui import DeferredAnalysis
from config_gui import Config
from data_handler import *
from networker import GlobalContextHandler, GlobalCertificateHandler

import zmq
import string

from validator import Validator

serverAddr = 'tcp://35.204.135.105'
localAddr = 'tcp://127.0.0.1'
registrationPort = ':5001'


class mainWindow(QMainWindow):
	def __init__(self, app):
		QMainWindow.__init__(self)
		self.app = app

		authenticated = False

		if os.path.exists("../userDetails.config"):
			authenticated = authenticateUserDetails()
		else:
			loginDialog = LoginDialog()
			authenticated, msg, userID, key = loginDialog.getUserData()
			
			self.saveUserDetails(userID, key)

		if authenticated:
			tabs = MainWindowTabs(app)
			self.setCentralWidget(tabs)
		else:
			self.closeEvent(None)

	def saveUserDetails()

	def closeEvent(self, event):
		activeThreads = threading.enumerate()
		for thread in activeThreads:
			if thread is not threading.currentThread():
				try:
					if thread.stop is False:
						thread.stop = True
						thread.join()
				except:
					pass

		certHandler = GlobalCertificateHandler.getInstance()
		publicPath, _ = certHandler.getCertificatesPaths()
		ctxHandler = GlobalContextHandler.getInstance(publicPath)
		ctxHandler.cleanup()

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
		usernameLayout.addWidget(usernameLabel)
		usernameLayout.addWidget(self.usernameEntryLogin)

		passwordLayout = QHBoxLayout()
		passwordLabel = QLabel("Password: ")
		self.passwordEntryLogin = QLineEdit()
		self.passwordEntryLogin.setEchoMode(QLineEdit.Password)
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
		usernameLabel = QLabel("Username: ")
		self.usernameEntryRegister = QLineEdit()
		self.usernameEntryRegister.setMaxLength(32)
		usernameLayout.addWidget(usernameLabel)
		usernameLayout.addWidget(self.usernameEntryRegister)

		emailLayout = QHBoxLayout()
		emailLabel = QLabel("Email: ")
		self.emailEntryRegister = QLineEdit()
		self.emailEntryRegister.setMaxLength(254)
		emailLayout.addWidget(emailLabel)
		emailLayout.addWidget(self.emailEntryRegister)

		passwordLayout = QHBoxLayout()
		passwordLabel = QLabel("Password: ")
		self.passwordEntryRegister = QLineEdit()
		self.passwordEntryRegister.setEchoMode(QLineEdit.Password)
		self.passwordEntryRegister.setMaxLength(128)
		passwordLayout.addWidget(passwordLabel)
		passwordLayout.addWidget(self.passwordEntryRegister)

		passConfLayout = QHBoxLayout()
		passConfLabel = QLabel("Confirm Password: ")
		self.passConfEntryRegister = QLineEdit()
		self.passConfEntryRegister.setEchoMode(QLineEdit.Password)
		self.passConfEntryRegister.setMaxLength(128)
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

		self.authenticated, self.msg = self.verifyUser(username, password)
		print(self.msg)
		if self.authenticated:
			self.accept()
		else:
			self.msgLabelLogin.setText(self.msg)

	def verifyUser(self, username, password):
		authenticated = False
		msg = ''

		socket = setupGlobalSocket(serverAddr + registrationPort)
		socket.send_string('LOGIN' + ' ' + username + ' ' + password)
		result = socket.recv_string()
		parts = result.split('  ')

		if parts[0] == 'True':
			authenticated = True
		else:
			authenticated = False

		return authenticated, parts[1]

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

			if len(data) == 3:
				userID = data[2]

			if registered:
				activationDialog = ActivationDialog()
				self.authenticated, self.msg = activationDialog.getKey(userID)
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
		socket = setupGlobalSocket(serverAddr + registrationPort)
		socket.send_string('REGISTER ' + username + ' ' + password + ' ' + email)
		print("sent")
		result = socket.recv_string()
		print(result)
		socket.close()

		parts = result.split('  ')
		result = parts[0]
		msg = parts[1]

		if result == 'True':
			return True, msg, parts[2]
		else:
			return False, msg

	def exit(self):
		sys.exit()

	def getUserData(self):
		self.exec()
		return self.authenticated, self.msg

	def closeEvent(self, event):
		sys.exit()


def setupGlobalSocket(addr):
	certHandler = GlobalCertificateHandler.getInstance()
	serverPath = certHandler.getServerKey()
	serverKey = zmq.auth.load_certificate(serverPath)[0]
	publicPath, privatePath = certHandler.getCertificatesPaths()
	ctxHandler = GlobalContextHandler.getInstance(publicPath)
	context = ctxHandler.getContext()

	socket = context.socket(zmq.REQ)
	privateFile = privatePath + "client-front.key_secret"
	publicKey, privateKey = zmq.auth.load_certificate(privateFile)
	socket.curve_secretkey = privateKey
	socket.curve_publickey = publicKey
	socket.curve_serverkey = serverKey

	socket.connect(serverAddr + registrationPort)

	return socket


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
		key = self.activationEntryRegister.text()
		validator = Validator()
		validKey, msg = validator.validateKey(key)

		if validKey:
			socket = setupGlobalSocket(serverAddr + registrationPort)
			socket.send_string('ACTIVATE ' + key + ' ' + self.userID)
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
				self.msgLabelActivate.setText(msg)
		else:
			self.msgLabelActivate.setText(msg)

	def cancel(self):
		self.reject()

	

	def getKey(self, userID):
		self.userID = userID
		self.exec()
		return self.authenticated, self.msg


class MainWindowTabs(QTabWidget):
	def __init__(self, app):
		QTabWidget.__init__(self)

		dataLoader = DataLoader()

		self.configTab = Config(app, dataLoader)
		self.liveTab = LiveAnalysis(app, dataLoader)
		self.deferredTab = DeferredAnalysis(app)

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

		self.currentChanged.connect(self.tabChanged)

	def tabChanged(self, index):
		if index == 0:
			print("config")
		elif index == 1:
			print("live")
		elif index == 2:
			print("deferred")
		else:
			print("Error getting index of new tab")

if __name__ == '__main__':
	app = QApplication(sys.argv)

	mainWindow = mainWindow(app)
	mainWindow.show()

	sys.exit(app.exec_())
