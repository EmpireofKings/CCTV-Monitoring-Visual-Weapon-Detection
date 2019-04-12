# Ben Ryan C15507277

import numpy as np
from PySide2.QtCore import *


class DisplayConnector(QObject):
	newFrameSignal = Signal(np.ndarray)

	def __init__(self, display):
		QObject.__init__(self)
		self.newFrameSignal.connect(display.updateDisplay)

	def emitFrame(self, frame):
		self.newFrameSignal.emit(frame)


class GenericConnector(QObject):
	signal = Signal(object)

	def __init__(self, func):
		QObject.__init__(self)
		self.signal.connect(func)

	def emitSignal(self, args=None):
		self.signal.emit(args)
