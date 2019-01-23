import numpy as np
import cv2
import sys
import json
import math
from pprint import pprint
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from threading import Thread
import time

class DeferredAnalysis():
	def __init__(self, helper):
		self.layout = QHBoxLayout()
		placeholder = QLabel("Deferred Analysis Placeholder")
		self.layout.addWidget(placeholder)

	def getLayout(self):
		return self.layout
