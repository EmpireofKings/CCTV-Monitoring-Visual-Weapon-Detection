import signal

class Terminator():
	def __init__(self):
		self.__terminating = False
		signal.signal(signal.SIGTERM, self.terminate)
		signal.signal(signal.SIGINT, self.terminate)

	def terminate(self, signal, frame):
		print("Termination signal received")
		self.__terminating = True

	def isTerminating(self):
		return self.__terminating
