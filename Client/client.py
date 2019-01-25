import sys
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from collections import deque

#my modules
import live
import deferred

class mainWindow(QMainWindow):
	def __init__(self, app):
		QMainWindow.__init__(self)
		items = ["Live Feed", "Existing Media"]

		decision, check = QInputDialog.getItem(self, "Analysis Type", "Please choose", items, editable=False)

		if check == False:
			sys.exit()

		mainWidget = QWidget()

		if decision == items[0]:
			liveAnalyser = live.LiveAnalysis(app)
			mainWidget.setLayout(liveAnalyser.getLayout())
		elif decision == items[1]:
			deferredAnalyser = deferred.DeferredAnalysis(app)
			mainWidget.setLayout(deferredAnalyser.getLayout())

		self.setCentralWidget(mainWidget)

if __name__ == '__main__':
	app = QApplication(sys.argv)

	mainWindow = mainWindow(app)
	mainWindow.show()

	sys.exit(app.exec_())
