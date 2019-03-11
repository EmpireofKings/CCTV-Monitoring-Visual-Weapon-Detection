import signal
import logging


class Terminator():
	__instance = None

	def __init__(self):
		self.__terminating = False
		signal.signal(signal.SIGTERM, self.terminate)
		signal.signal(signal.SIGINT, self.terminate)
		logging.info('Terminator signals linked')

	@staticmethod
	def getInstance():
		if Terminator.__instance is None:
			Terminator.__instance = Terminator()

		return Terminator.__instance

	def terminate(self, signal, frame):
		logging.info('Termination signal received, please wait.')
		self.__terminating = True

	def autoTerminate(self):
		self.terminate(signal.SIGTERM, None)

	def isTerminating(self):
		return self.__terminating

