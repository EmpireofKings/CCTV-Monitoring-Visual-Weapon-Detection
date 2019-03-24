from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from terminator import Terminator
import os
import sys


class CornerControls(QPushButton):
	def __init__(self, app):
		QPushButton.__init__(self)
		self.app = app
		# logoutButton = QPushButton('Logout')
		# logoutButton.clicked.connect(self.logout)

		# outerLayout = QHBoxLayout()
		# outerLayout.addWidget(logoutButton)

		# self.setLayout(outerLayout)
		self.setText('Logout')
		self.clicked.connect(self.logout)

	def logout(self):
		terminator = Terminator.getInstance()

		dialog = QMessageBox()
		dialog.setWindowTitle("Logout")
		dialog.setText("Are you sure?")
		yesButton = QMessageBox.Yes
		dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

		ans = dialog.exec()

		if 'Yes' in dialog.clickedButton().text():
			os.remove('../userDetails.config')
			terminator.autoTerminate()
			self.app.exit()
			sys.exit

