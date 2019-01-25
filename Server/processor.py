from collections import deque
import tensorflow as tf
import _pickle as pickle
from pprint import pprint

class FrameProcessor():
	def __init__(self, recvBuffer):
		self.recvBuffer = recvBuffer
		self.processReady = deque()
		self.model = tf.keras.models.load_model('../Models/model-current.h5')

	def unbundle(self):
		while True:
			if self.recvBuffer:
				data = self.recvBuffer.pop()
				#print(data)
				framePacks = data.split(b'IMAGE_BORDER')
				#pprint(framePacks)
				batch = []
				for framePack in framePacks:
					#print(framePack)
					framePack = pickle.loads(framePack)
					batch.append(framePack.getFrameAsndarray)

				self.processReady.append(batch)
				print(len(processReady),"    " ,len(recvBuffer))

		#take batches recevied from buffer, split to individual frame packs
		#place in deque for processing

	def process(self):
		if self.model is None:
			print("model not loaded")
			return
		print("Process thread ready with following model:")
		self.model.summary()

		while True:
			if self.processReady:
				batch = self.processReady.pop()

			#run frames through neural network
			#package results with corresponding frames
			#place in queue to send back to client
