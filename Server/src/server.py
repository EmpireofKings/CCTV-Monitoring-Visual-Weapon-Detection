#TODO

from threading import Thread
from collections import deque
import socket as s
import tensorflow as tf
import cv2
import numpy as np
import _pickle as pickle
import sys
import zmq
import base64 as b64
import tensorflow as tf

class Receiver(Thread):
	def __init__(self, addr):
		Thread.__init__(self)

		context = zmq.Context()
		self.socket = context.socket(zmq.REP)
		self.socket.bind(addr)

		print("Listening on", addr)

	def run(self):
		model = tf.keras.models.load_model("../../Models/model-current.h5")
		model.summary()

		while True:
			received = self.socket.recv_string()
			jpegStr = b64.b64decode(received)
			jpeg = np.fromstring(jpegStr, dtype=np.uint8)
			frame = cv2.imdecode(jpeg, 1)

			frameArr = np.asarray(frame)
			frameArr = np.expand_dims(frameArr, axis=0)
			results = model.predict(frameArr)

			labels = {	"0" : "Clear",
						"1" : "Knife",
						"2" : "Pistol",
						"3" : "Long Gun"}

			for i in range(4):
				result = results[0][i]

				# if result > .5:
				# 	print(labels.get(str(i)), str(result))


			#encoded = b64.b64encode(result)
			self.socket.send_string(str(results))



if __name__ == '__main__':
	responseQueues = {}
	receiver = Receiver('tcp://0.0.0.0:5000')
	receiver.start()
