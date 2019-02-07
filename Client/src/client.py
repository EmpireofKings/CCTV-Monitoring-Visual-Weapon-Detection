#TODO

import sys
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import threading


import live as l
import deferred as d
import config as c

class mainWindow(QMainWindow):
	def __init__(self, app):
		QMainWindow.__init__(self)
		items = ["Live Feed", "Existing Media"]

		config = c.Config(app)
		live = l.LiveAnalysis(app)
		deferred = d.DeferredAnalysis(app)

		#Icons acquired from www.flaticon.com licensed by Creative Commons BY 3.0 http://creativecommons.org/licenses/by/3.0/
		configIcon = QIcon("../data/icons/config.png") #Icon made by Fermam Aziz  https://www.flaticon.com/authors/fermam-aziz
		liveIcon = QIcon("../data/icons/live.png") #Icon made by photo3idea_studio https://www.flaticon.com/authors/photo3idea-studio
		deferredIcon = QIcon("../data/icons/deferred.png") #Icon made by Smashicons https://www.flaticon.com/authors/smashicons

		tabs = QTabWidget()
		tabs.addTab(config, configIcon, "Configuration")
		tabs.addTab(live, liveIcon, "Live Analysis")
		tabs.addTab(deferred, deferredIcon, "Deferred Analysis")

		self.setCentralWidget(tabs)

	#override close event to ensure all threads terminate themselves before main thread terminates
	#otherwise threads that still run after main thread terminates will throw many errors
	def closeEvent(self, event):
		activeThreads = threading.enumerate()
		for thread in activeThreads:
			if thread is not threading.currentThread():
				thread.stop = True
				thread.join()

		sys.exit()

if __name__ == '__main__':
	app = QApplication(sys.argv)

	mainWindow = mainWindow(app)
	mainWindow.show()

	sys.exit(app.exec_())
