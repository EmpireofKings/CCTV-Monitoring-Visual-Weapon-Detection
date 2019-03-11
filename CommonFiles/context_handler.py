import zmq
from zmq.auth.thread import ThreadAuthenticator


class ContextHandler():
	def __init__(self, publicPath):
		self.__context = zmq.Context()
		self.publicPath = publicPath

		self.auth = ThreadAuthenticator(self.__context)
		self.auth.start()
		self.auth.configure_curve(domain='*', location=self.publicPath)
		self.auth.thread.setName("CurveAuth")

	def getContext(self):
		return self.__context

	def configureAuth(self):
		self.auth.configure_curve(domain='*', location=self.publicPath)

	def cleanup(self):
		self.__context.destroy()
