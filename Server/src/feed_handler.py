from results_handler import ResultsHandler
from feed_process_helper import FeedProcessHelper
from terminator import Terminator
from certificate_handler import CertificateHandler
from context_handler import ContextHandler
import zmq
from monitor import Monitor
import base64 as b64
from threading import Thread

class FeedHandler(Thread):
	def __init__(self, feedID):
		Thread.__init__(self)

		self.terminator = Terminator.getInstance()

		self.certHandler = CertificateHandler(id=feedID)
		publicPath, privatePath = self.certHandler.getCertificatesPaths()

		self.ctxHandler = ContextHandler(publicPath)
		context = self.ctxHandler.getContext()

		self.socket = context.socket(zmq.REP)
		monitorSocket = self.socket.get_monitor_socket()
		self.monitor = Monitor(monitorSocket, feedID)
		self.monitor.setDaemon(True)
		self.monitor.start()

		privateFile = privatePath + "server-" + feedID + ".key_secret"
		self.publicKey, privateKey = zmq.auth.load_certificate(privateFile)
		self.socket.curve_secretkey = privateKey
		self.socket.curve_publickey = self.publicKey
		self.socket.curve_server = True

		self.port = self.socket.bind_to_random_port('tcp://*',
													min_port=49151,
													max_port=65535)
		self.feedID = feedID

	def getPort(self):
		return self.port

	def getPublicKey(self):
		return self.publicKey

	def run(self):
		helper = Helper()
		global model
		global session
		global graph

		resultHandler = ResultsHandler(9, 30)
		# bgRemover = BackgroundRemover(feed)

		self.socket.setsockopt(zmq.RCVTIMEO, 60000)
		with session.as_default():
			with graph.as_default():
				while not self.terminator.isTerminating():
					try:
						received = self.socket.recv_string()
					except:
						break

					jpegStr = b64.b64decode(received)
					jpeg = np.fromstring(jpegStr, dtype=np.uint8)
					frame = cv2.imdecode(jpeg, 1)

					regions, drawCoords = helper.extractRegions(frame, 3, (64, 64), True)
					results = np.around(model.predict(regions)[:, 10:], decimals=3)
					resultHandler.append(results)
					alert = resultHandler.assess()

					# frame = bgRemover.drawBoundingBox(frame)

					self.socket.send_string(str(alert))

		self.monitor.stop = True
		self.socket.disable_monitor()
		self.socket.close()
		self.ctxHandler.cleanup()
		self.certHandler.cleanup()
		print("Ending thread", self.feedID)
