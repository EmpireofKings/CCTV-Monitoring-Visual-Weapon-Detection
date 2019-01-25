import sys
import os
from pathlib import Path
CommonPath = str(Path(str(os.path.dirname(os.path.realpath(__file__)))).parent) + "/Common"
sys.path.append(CommonPath)

import numpy as np
import cv2
import tensorflow as tf
import clientServer as cs
from threading import Thread
import time
import sharedParams as sp

latestFrame = None
inBuff = cs.queue.Queue()
outBuff = cs.queue.Queue()

dataStreaming = False

#main function on main thread
def main():
	readSocket = setupSocket(cs.INTHOST, cs.upStreamPort)
	respSocket = setupSocket(cs.INTHOST, cs.downStreamPort)

	PrintThread = Thread(target=cs.displayMessages, name="PrintThread")
	ReceiveThread = Thread(target=receiveThreadMain, name="ReceiveThread", args=[readSocket])
	ProcessThread = Thread(target=processThreadMain, name="ProcessThread")
	ResponseThread = Thread(target=responseThreadMain, name="ResponseThread",args=[respSocket])

	PrintThread.start()
	ReceiveThread.start()
	ProcessThread.start()
	ResponseThread.start()

#main function on thread for receiving frames from client
def receiveThreadMain(socket):
	global latestFrame, dataStreaming
	while True:
		cs.messages.put("Read thread ready. Listening on: " + cs.INTHOST + ":" + str(cs.upStreamPort))

		conn, addr = socket.accept()
		cs.messages.put("Connection on read thread. (" + str(addr) + ")")

		cs.expectedSize = int(initCommsUp(conn))
		cs.messages.put("Expected Size " + str(cs.expectedSize))
		dataStreaming = True
		while conn is not None:
			data, conn = cs.recvFrame(conn)

			if data is cs.COMPLETE:
				conn.close()
				dataStreaming = False
				break

			inBuff.put(data)
			latestFrame = data


#main function on thread for processing frames
def processThreadMain():
	global latestFrame, inBuff, outBuff

	model = tf.keras.models.load_model('../Models/model-0.h5')
	model.summary()
	#model.compile(optimizer=tf.train.AdamOptimizer(), loss='binary_crossentropy', metrics=['accuracy'])

	cs.messages.put("Process thread ready.")

	negativeCount = 0
	positiveCount = 0
	while True:

		# while inBuff.empty() == True : True

		# frame = inBuff.get()


		while latestFrame is None : True

		frame = latestFrame
		latestFrame = None

		# shp = np.shape(frame)
		# h = shp[0]
		# w = shp[1]
		# c = (int(h/2), int(w/2))
		# y1 = c[0]-50
		# y2 = c[0]+50
		# x1 = c[1]-50
		# x2 = c[1]+50

		#frameCrop = frame[y1:y2,x1:x2]
		frameArr = np.asarray(frame)
		frameArr = np.expand_dims(frameArr, axis=0)
		res = model.predict(frameArr)[0][0]

		frameCopy = cv2.resize(frame, sp.displaySize)

		if res < .4:
			#cv2.imshow("Negative", frameCopy)
			cv2.putText(frameCopy, "N:" + str(res),(50,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 2)
		elif res >= .4:
			#cv2.imshow("Positive", frameCopy)
			cv2.putText(frameCopy, "P:" + str(res),(50,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 2)

		#cv2.waitKey(0)


		#canny = cv2.Canny(frame, 128,255)

	#	thresh = np.mean(frame) + np.std(frame)
	#	_, frame = cv2.threshold(frame, thresh, 255, cv2.THRESH_BINARY)
		#frame = cv2.adaptiveThreshold(frame, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)

		# _, contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		# frame = cv2.drawContours(frame, contours, -1, (0,0,255), 1)

		#frame = cv2.UMat.get(frame)
		outBuff.put(frameCopy)

#main function on thread for sending processed frames to client
def responseThreadMain(socket):
	global outBuff, dataStreaming

	while True:
		cs.messages.put("Response thread ready. Listening on:" + cs.INTHOST + ":" + str(cs.downStreamPort))

		conn, addr = socket.accept()
		cs.messages.put("Connection on response thread. (" + str(addr) +")")

		check, frame = initCommsDown(conn)

		if check != True:
			return

		while True:
			cs.sendFrame(frame, conn)

			if (outBuff.empty() == True and dataStreaming == False):
				cs.sendFrame(cs.COMPLETE, conn)
				conn.close()
				break
			#might get caught here when video ends
			while outBuff.empty() == True: True
			frame = outBuff.get()

#used by response thread
def initCommsDown(socket):
	global outBuff

	while True:
		if outBuff.empty() == False:
			frame = outBuff.get()
			frameSerial = cs.pickle.dumps(frame)
			# _, frameSerial = cv2.imencode('.jpg',frame)
			length = len(frameSerial)
			cs.sendMessage(length, socket)

			resp, _ = cs.recvMessage(socket)
			if resp == cs.READY:
				cs.messages.put("Downstream comms initialised")
				return True, frame

	return False, None

#used by receive thread
def initCommsUp(socket):
	msg, _ = cs.recvMessage(socket)
	if msg == cs.NOTREADY:
		return

	cs.sendMessage(cs.READY, socket)

	return msg

#used by main thread
def setupSocket(HOST, PORT):
	socket = cs.sock.socket(cs.sock.AF_INET, cs.sock.SOCK_STREAM)
	socket.bind((HOST, PORT))
	socket.listen()
	return socket

if __name__ == '__main__':
	main()
