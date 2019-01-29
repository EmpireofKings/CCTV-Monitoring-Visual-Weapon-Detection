
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
		#self.socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))

		print("Listening on", addr)

	def run(self):
		model = tf.keras.models.load_model("../Models/model-current.h5")
		model.summary()

		while True:
			received = self.socket.recv_string()
			jpegStr = b64.b64decode(received)
			jpeg = np.fromstring(jpegStr, dtype=np.uint8)
			frame = cv2.imdecode(jpeg, 1)

			frame = cv2.resize(frame, (100,100)) #work it so it can use process size of (256, 144)
			frameArr = np.asarray(frame)
			frameArr = np.expand_dims(frameArr, axis=0)
			result = str(model.predict(frameArr)[0][0])

			#encoded = b64.b64encode(result)
			self.socket.send_string(result)

# class Receiver(Thread):
# 	def __init__(self, conn, addr, feedID):
# 		Thread.__init__(self)
#
# 		self.conn = conn
# 		self.addr = addr
# 		self.feedID = feedID
#
# 		print("Thread ready:", str(self.addr[0]) +":"+str(self.addr[1])+":"+str(self.feedID))
#
# 		self.processQueue = deque()
# 		processor = Processor(self.processQueue, self.feedID)
# 		processor.start()
#
# 	def run(self):
# 		overflow = b''
# 		while self.conn is not None:
# 			data = overflow
# 			overflow = b''
#
# 			while True:
# 				data += self.conn.recv(8096)
#
# 				if b'\x94t\x94b.' in data:
# 					index = data.index(b'\x94t\x94b.')
# 					overflow = data[index+len(b'\x94t\x94b.'):]
# 					data = data[:index+len(b'\x94t\x94b.')]
# 					#print(data[len(data)-20:])
# 					break
#
# 			unpick = pickle.loads(data)
# 			self.processQueue.append(unpick)
			#print(self.feedID, "Received:", len(data))

# class Listener(Thread):
# 	def __init__(self, addr):
# 		Thread.__init__(self)
#
# 		self.socket = s.socket(s.AF_INET, s.SOCK_STREAM)
# 		self.socket.bind(addr)
# 		self.socket.listen()
#
# 		print("Listening on", addr)
#
# 	def run(self):
# 		while self.socket is not None:
# 			conn, addr = self.socket.accept()
#
# 			feedID = b''
# 			type = ''
#
# 			while True:
# 				feedID += conn.recv(16)
#
# 				if b'END' in feedID:
# 					msg = feedID[:(len(feedID)-len('END'))].decode('utf-8')
# 					type = msg[len(msg)-len('Resp'):]
# 					feedID = feedID[:(len(feedID)-len('RespEND'))].decode('utf-8')
# 					break;
#
# 			if type == 'Recv':
# 				receiver = Receiver(conn, addr, feedID)
# 				receiver.start()
# 			elif type == 'Resp':
# 				responder = Responder(conn, addr, feedID)
# 				responder.start()
# 			else:
# 				print("Error handing off connection to new thread")

# class Receiver(Thread):
# 	def __init__(self, conn, addr, feedID):
# 		Thread.__init__(self)
#
# 		self.conn = conn
# 		self.addr = addr
# 		self.feedID = feedID
#
# 		print("Thread ready:", str(self.addr[0]) +":"+str(self.addr[1])+":"+str(self.feedID))
#
# 		self.processQueue = deque()
# 		processor = Processor(self.processQueue, self.feedID)
# 		processor.start()
#
# 	def run(self):
# 		overflow = b''
# 		while self.conn is not None:
# 			data = overflow
# 			overflow = b''
#
# 			while True:
# 				data += self.conn.recv(8096)
#
# 				if b'\x94t\x94b.' in data:
# 					index = data.index(b'\x94t\x94b.')
# 					overflow = data[index+len(b'\x94t\x94b.'):]
# 					data = data[:index+len(b'\x94t\x94b.')]
# 					#print(data[len(data)-20:])
# 					break
#
# 			unpick = pickle.loads(data)
# 			self.processQueue.append(unpick)
# 			#print(self.feedID, "Received:", len(data))
#
# class Processor(Thread):
# 	def __init__(self, queue, feedID):
# 		Thread.__init__(self)
#
# 		self.queue = queue
# 		self.feedID = feedID
#
# 		self.responseQueue = deque()
# 		global responseQueues
# 		responseQueues[feedID] = self.responseQueue
#
# 	def run(self):
# 		# global model
# 		# global graph
# 		# with graph.as_default():
# 			while True:
# 				if self.queue:
# 					frameBytes = self.queue.pop()
# 					# frameArr = np.fromstring(frameBytes, np.uint8)
# 					# frameArr = cv2.imdecode(frameArr, cv2.IMREAD_COLOR)
# 					# frameCopy = frameArr.copy()
# 					# frameArr = np.asarray(frameArr)
# 					# frameArr = np.expand_dims(frameArr, axis=0)
# 					#
# 					# result = model.predict(frameArr)[0][0]
# 					#
# 					# displayFrame = cv2.resize(frameCopy, (256, 144))
# 					#
# 					# if result < .4:
# 					# 	#cv2.imshow("Negative", frameCopy)
# 					# 	cv2.putText(frameCopy, "N:" + str(result),(50,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2)
# 					# elif result >= .4:
# 					# 	#cv2.imshow("Positive", frameCopy)
# 					# 	cv2.putText(frameCopy, "P:" + str(result),(50,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)
# 					#
# 					# _, encoded = cv2.imencode('.jpg', frameCopy)
# 					# encoded = encoded.tostring()
#
# 					pickled = pickle.dumps(frameBytes, protocol=4)
# 					self.responseQueue.append(pickled)
#
# 				#	print(self.feedID, result)
#
# class Responder(Thread):
# 	def __init__(self, conn, addr, feedID):
# 		Thread.__init__(self)
# 		self.conn = conn
# 		self.addr = addr
# 		self.feedID = feedID
#
# 		global responseQueues
#
# 		#wait until the process queue has created a deque for us
# 		while feedID not in responseQueues: True
#
# 		self.queue = responseQueues.get(feedID)
#
# 	def run(self):
# 		while True:
# 			if self.queue:
# 				frame = self.queue.pop()
#
# 				total = len(frame)
# 				sent = 0
#
# 				while sent < total:
# 					sent += self.conn.send(frame[sent:])
#

if __name__ == '__main__':
#	model = tf.keras.models.load_model("../Models/model-current.h5")
#	graph = tf.get_default_graph()

	responseQueues = {}
	receiver = Receiver('tcp://0.0.0.0:5000')
	receiver.start()

	# respondPortListener = Listener(('localhost', 5001))
	# respondPortListener.start()
