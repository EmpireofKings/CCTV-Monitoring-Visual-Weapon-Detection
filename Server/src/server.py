# TODO

import base64 as b64
import logging
import os
import shutil
import signal
import socket as s
import sys
import threading
import time
from collections import deque
from threading import Thread

import cv2
import numpy as np
import tensorflow as tf
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
from zmq.utils.monitor import recv_monitor_message

import _pickle as pickle
from authenticator import AuthenticationListener
from certificate_handler import CertificateHandler
from context_handler import ContextHandler
from feed_listener import FeedListener
from monitor import Monitor
from terminator import Terminator

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
			[logging.FileHandler('./Logs/server_logs.txt'),
			logging.StreamHandler(sys.stdout)])

	logging.info('\n\n\n\t\tBegin new set of logs:\n\n\n')

	terminator = Terminator.getInstance()

	try:
		model = tf.keras.models.load_model("../../Decent Models/model-current.h5")
		model._make_predict_function()
		session = tf.keras.backend.get_session()
		graph = tf.get_default_graph()
		graph.finalize()
		logging.debug('Model/Graph ready')
	except:
		logging.critical('Exception loading model/graph', exc_info=True)
		terminator.autoTerminate()

	try:
		feedListener = FeedListener('tcp://0.0.0.0:5000')
		feedListener.setDaemon(True)
		feedListener.start()
		logging.debug('Feed listener thread started')
	except:
		logging.critical(
			'Exception occured starting feed listener thread',
			exc_info=True)
		terminator.autoTerminate()

	try:
		authListener = AuthenticationListener()
		authListener.setDaemon(True)
		authListener.start()
		logging.debug('Authentication thread started')
	except:
		logging.critical('Exception occured starting auth thread', exc_info=True)
		terminator.autoTerminate()

	while not terminator.isTerminating():
		time.sleep(5)

	logging.debug('Main thread ending')
