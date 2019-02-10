class Networker(Thread):
	def __init__(self, feedData, display, mainDisplay):
		Thread.__init__(self)

		self.stop = False
		self.feedData = feedData
		self.display = display
		self.mainDisplay = mainDisplay

	def setup(self):
		serverAddr = 'tcp://35.204.135.105:5000'
		localAddr = 'tcp://127.0.0.1:5000'

		context = zmq.Context()
		self.socket = context.socket(zmq.REQ)
		self.socket.connect(localAddr)

	def run(self):
		global nextFrames
		global mainFeedID
		self.setup()

		while self.stop is False:
			frames = nextFrames.get(str(self.feedData["id"]))

			if frames is not None:
				self.socket.send(frames[0])

				result = self.socket.recv_string()
				#print(self.feedID, result)

				self.display.newFrameSignal.emit(frames[1])

				#if this display is the main, emit the frame signal to both displays
				if self.feedData["id"] == mainFeedID:
					self.mainDisplay.newFrameSignal.emit(frames[1])
					self.mainDisplay.feedData = self.feedData
