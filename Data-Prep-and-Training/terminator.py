# Ben Ryan C15507277

import signal


class Terminator():
	__instance = None

	def __init__(self):
		self.__terminating = False
		signal.signal(signal.SIGTERM, self.terminate)
		signal.signal(signal.SIGINT, self.terminate)

	@staticmethod
	def getInstance():
		if Terminator.__instance is None:
			Terminator.__instance = Terminator()

		return Terminator.__instance

	def terminate(self, signal, frame):
		print("Termination signal received. Please wait while clean up occurs.")
		self.__terminating = True

	def isTerminating(self):
		return self.__terminating
