#TODO

import sys
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from collections import deque

#my modules
import live
import deferred
import threading

class mainWindow(QMainWindow):
	def __init__(self, app):
		QMainWindow.__init__(self)
		items = ["Live Feed", "Existing Media"]

		decision, check = QInputDialog.getItem(self, "Analysis Type", "Please choose", items, editable=False)

		if check == False:
			sys.exit()

		mainWidget = None

		if decision == items[0]:
			mainWidget = live.LiveAnalysis(app)
		elif decision == items[1]:
			mainWidget = deferred.DeferredAnalysis(app)

		self.setCentralWidget(mainWidget)

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
