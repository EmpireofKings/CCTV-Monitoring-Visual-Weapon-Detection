class FeedLoader(Thread):
	#GUI Thread launches this thread
	#to prevent holding GUI Thread for too long keep __init__ minimal
	def __init__(self, feedData):
		Thread.__init__(self)

		self.stop = False
		self.feedData = feedData

	def setup(self):
		if self.feedData["id"].isdigit():
			self.feed = cv2.VideoCapture(int(self.feedData["id"]))
		else:
			self.feed = cv2.VideoCapture(self.feedData["id"])

		self.FPS = self.feed.get(cv2.CAP_PROP_FPS)

	def run(self):
		global nextFrames
		displaySize = (640, 360)
		processSize = (256, 144)

		self.setup()

		timer = time.time()
		while self.feed.isOpened() and self.stop is False:
			while time.time() - timer < 1/self.FPS : time.sleep(0.01)
			loadCheck, frame = self.feed.read()
			timer = time.time()

			if loadCheck:
				frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
				displayFrame = cv2.resize(frame, displaySize)
				processFrame = cv2.resize(frame, processSize)


				pmap = QPixmap.fromImage(QImage(displayFrame.data, displaySize[0], displaySize[1], 3*displaySize[0],  QImage.Format_RGB888))

				encodeCheck, jpegBuf = cv2.imencode('.jpg', processFrame)

				if encodeCheck:
					encoded = b64.b64encode(jpegBuf)
					nextFrames[str(self.feedData["id"])] = (encoded, pmap)
			else:
				self.feed.set(cv2.CAP_PROP_POS_FRAMES, 0)
