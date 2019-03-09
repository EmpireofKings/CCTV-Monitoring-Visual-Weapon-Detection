import zmq
from zmq.auth.thread import ThreadAuthenticator


class ContextHandler():
	def __init__(self, publicPath):
		self.__context = zmq.Context()
		auth = ThreadAuthenticator(self.__context)
		auth.start()
		auth.configure_curve(domain='*', location=publicPath)

	def getContext(self):
		return self.__context

	def cleanup(self):
		self.__context.destroy()
