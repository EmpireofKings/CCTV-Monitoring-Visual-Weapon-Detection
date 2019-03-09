# TODO

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


class mainWindow(QMainWindow):
	def __init__(self, app):
		loginDialog = LoginDialog()
		result = loginDialog.getUserData()
		print(result)
		QMainWindow.__init__(self)
		self.app = app
		tabs = MainWindowTabs(app)
		self.setCentralWidget(tabs)


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
		# sys.exit()


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
		loginTab.setLayout(outerLoginLayout)

		return loginTab

	def setupRegisterTab(self):
		registerTab = QWidget()

		usernameLayout = QHBoxLayout()
		usernameLabel = QLabel("Username: ")
		self.usernameEntryRegister = QLineEdit()
		usernameLayout.addWidget(usernameLabel)
		usernameLayout.addWidget(self.usernameEntryRegister)

		emailLayout = QHBoxLayout()
		emailLabel = QLabel("Email: ")
		self.emailEntryRegister = QLineEdit()
		emailLayout.addWidget(emailLabel)
		emailLayout.addWidget(self.emailEntryRegister)

		passwordLayout = QHBoxLayout()
		passwordLabel = QLabel("Password: ")
		self.passwordEntryRegister = QLineEdit()
		self.passwordEntryRegister.setEchoMode(QLineEdit.Password)
		passwordLayout.addWidget(passwordLabel)
		passwordLayout.addWidget(self.passwordEntryRegister)

		activationLayout = QHBoxLayout()
		activationLabel = QLabel("Activation Key: ")
		self.activationEntryRegister = QLineEdit()
		activationLayout.addWidget(activationLabel)
		activationLayout.addWidget(self.activationEntryRegister)

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
		outerRegisterLayout.addLayout(activationLayout)
		outerRegisterLayout.addLayout(buttonLayout)
		registerTab.setLayout(outerRegisterLayout)

		return registerTab

	def login(self):
		username = self.usernameEntryLogin.displayText()
		password = self.passwordEntryLogin.displayText()

		verified, msg = self.verifyUser(username, password)

		if verified:
			self.accept()
		else:
			self.msgLabelLogin.setText(msg)

		self.accept()

	def verifyUser(username, password):
		return False, "Could not authenticate"

	def validateUsername(self, username):
		valid = True
		msg = ''

		if username is None:
			valid = False
			msg += '\nUsername must not be blank'

		if len(username) < 8:
			valid = False
			msg += '\nUsername must be at least 8 characters long'


	def validatePassword(self, password):

	def validateEmail(self, email):

	def validateKey(self, key):


	def register(self):
		username = self.usernameEntryRegister.displayText()
		password = self.passwordEntryRegister.displayText()
		email = self.emailEntryRegiter.displayText()
		activationKey = self.activationEntryRegister.displayText()

		validParameters = True
		msg = ''

		if not self.validateUsername(username):
			validParameters = False
			msg += "\nUsername invalid"  # TODO + reqs

		if not self.validatePassword(password):
			validParameters = False
			msg += "\nPassword invalid"  # TODO + reqs

		if not self.validateEmail(email):
			validParameters = False
			msg += "\nEmail invalid"  # TODO + reqs

		if not self.validateKey(activationKey):
			validParameters = False
			msg += "\nActivation Key invalid"  # TODO + reqs

		if validParameters:
			registered, msg = self.registerUser(
				username,
				password,
				email,
				activationKey)

			if registered:
				self.accept()
			else:
				self.msgLabelRegister.setText(msg)

	def registerUser(self, username, password, email, activationKey):
		return False, "Could not register"

	def exit(self):
		sys.exit()

	def getUserData(self):
		self.exec()
		return self.result

	def closeEvent(self, event):
		sys.exit()

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
