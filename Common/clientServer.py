import _pickle as pickle
import socket as sock
import cv2
import queue
import numpy as np

READY    = 'CODE:READY######'
NOTREADY = 'CODE:NOTREADY###'
COMPLETE = 'CODE:COMPLETE###'

EXTHOST = '35.204.94.151'
INTHOST = '10.164.0.3'

upStreamPort = 5000
downStreamPort = 5001
stdBuffSize = 26
stdMsgSize = 16
expectedSize = 0

messages = queue.Queue()

def displayMessages():
	global messages

	while True:
		while messages.empty() == True : True

		msg = messages.get()

		print(msg)

def sendMessage(msg, socket):
	msg = str(msg)
	msgLen = len(msg)

	if msgLen < stdMsgSize:
		diff = stdMsgSize- msgLen
		msg += ''.join(['*']*diff)

	serial = pickle.dumps(msg)
	length = len(serial)
	sentTotal = 0

	try:
		while sentTotal < length:
			sentAmt = socket.send(serial[sentTotal:])
			sentTotal += sentAmt
	except (ConnectionResetError, ConnectionRefusedError) as e:
		print(e)
		socket.close()
		return None, None

	return sentTotal, socket

def sendFrame(frame, socket):
	serial = pickle.dumps(frame)
	# _, serial = cv2.imencode('.jpg', frame)
	length = len(serial)

	sentTotal = 0
	try:
		while sentTotal < length:
			sentAmt = socket.send(serial[sentTotal:])
			sentTotal += sentAmt
	except (ConnectionResetError, ConnectionRefusedError) as e:
		print(e)
		socket.close()
		return None, None

	return sentTotal, socket


def recvMessage(socket):
	received = 0
	serial = b''

	try:
		while received < stdBuffSize:
			serial += socket.recv(stdBuffSize)
			received = len(serial)
	except (ConnectionResetError, ConnectionRefusedError) as e:
		print(e)
		socket.close()
		return None, None

	try:
		data = pickle.loads(serial)
		data = data.replace('*','')
		return data, socket
	except pickle.UnpicklingError as e:
		print(E)
		return None, None


overflow = None
def recvFrame(socket):
	global overflow
	received = 0
	data = b''

	try:
		if overflow is not None:
			data = overflow
			overflow = None

		while received < expectedSize:
			data += socket.recv(expectedSize)
			received = len(data)

		if received > expectedSize:
			overflow = data[expectedSize:received]
			data = data[:expectedSize]

	except (ConnectionResetError, ConnectionRefusedError) as e:
		print(e)
		#socket.close()
		return None, None

	try:
		data = pickle.loads(data)
		# data = np.fromstring(data, np.uint8)
		# data = cv2.imdecode(data, False)
		return data, socket
	except pickle.UnpicklingError as e:
		print(e)
		return None, None

def showFrame(title, frame, hold, time=0):
	cv2.imshow(title, frame)

	if hold == True:
		cv2.waitKey(time)

if __name__ == '__main__':
	True
