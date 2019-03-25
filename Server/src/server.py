# TODO

import logging
import os
import sys
import time

import tensorflow as tf

# Appending CommonFiles to system path for importing
# relatively messy but not many options to do this.
path = os.getcwd().split('/')
print(path)
path = '/'.join(path[:len(path) - 2])
sys.path.append(path + '/CommonFiles')

print(sys.path)

from authenticator import AuthenticationListener
from enroller import Enroller
from certificate_handler import CertificateHandler
from context_handler import ContextHandler
from feed_listener import FeedListener
from terminator import Terminator
from modelHandler import ModelHandler



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
		handlers=[
			logging.FileHandler('../Logs/server_logs.txt'),
			logging.StreamHandler(sys.stdout)])

	logging.info('\n\n\n\t\tBegin new set of logs:\n\n\n')

	terminator = Terminator.getInstance()

	certHandler = CertificateHandler('front', 'server')
	certHandler.prep()

	try:
		modelHandler = ModelHandler.getInstance()
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

	try:
		enroller = Enroller(feedListener, authListener)
		enroller.setDaemon(True)
		enroller.start()
		logging.debug('Enroller thread started')
	except:
		logging.critical(
			'Exception occured starting enroller thread',
			exc_info=True)
		terminator.autoTerminate()

	while not terminator.isTerminating():
		time.sleep(5)

	logging.debug('Main thread ending')
