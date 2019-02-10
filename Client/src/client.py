#TODO

import sys
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import threading

#from live_gui import LiveAnalysis
from deferred_gui import DeferredAnalysis
from config_gui import Config

class mainWindow(QMainWindow):
	def __init__(self, app):
		QMainWindow.__init__(self)
		#self.setMinimumSize(QSize(1280,600))

		tabs = Tab(app)
		self.setCentralWidget(tabs)

	def closeEvent(self, event):
		activeThreads = threading.enumerate()
		for thread in activeThreads:
			if thread is not threading.currentThread():
				thread.stop = True
				thread.join()

		sys.exit()

class Tab(QTabWidget):
	def __init__(self, app):
		QTabWidget.__init__(self)

		self.configTab = Config(app)
		#self.liveTab = LiveAnalysis(app)
		self.deferredTab = DeferredAnalysis(app)

		#Icons acquired from www.flaticon.com licensed by Creative Commons BY 3.0 http://creativecommons.org/licenses/by/3.0/
		configIcon = QIcon("../data/icons/config.png") #Icon made by Fermam Aziz  https://www.flaticon.com/authors/fermam-aziz
		#liveIcon = QIcon("../data/icons/live.png") #Icon made by photo3idea_studio https://www.flaticon.com/authors/photo3idea-studio
		deferredIcon = QIcon("../data/icons/deferred.png") #Icon made by Smashicons https://www.flaticon.com/authors/smashicons

		self.addTab(self.configTab, configIcon, "Configuration")
		#self.addTab(self.liveTab, liveIcon, "Live Analysis")
		self.addTab(self.deferredTab, deferredIcon, "Deferred Analysis")

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
