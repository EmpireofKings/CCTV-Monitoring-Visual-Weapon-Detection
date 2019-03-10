import zmq
from zmq.auth.thread import ThreadAuthenticator


class ContextHandler():
	def __init__(self, publicPath):
		self.__context = zmq.Context()
		self.auth = ThreadAuthenticator(self.__context)
		self.auth.start()
		self.auth.configure_curve(domain='*', location=publicPath)
		self.auth.thread.setName("CurveAuth")
	def getContext(self):
		return self.__context

	def cleanup(self):
		self.__context.destroy()
