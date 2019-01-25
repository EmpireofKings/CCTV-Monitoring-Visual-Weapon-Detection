from threading import Thread
from collections import deque
import socket as s

#my modules

class Listener(Thread):
	def __init__(self, addr):
		Thread.__init__(self)

		self.socket = s.socket(s.AF_INET, s.SOCK_STREAM)
		self.socket.bind(addr)
		self.socket.listen()

		print("Listening on", addr)

	def run(self):
		while self.socket is not None:
			conn, addr = self.socket.accept()

			feedID = b''

			while True:
				feedID += conn.recv(16)

				if b'END' in feedID:
					feedID = feedID[:(len(feedID)-len('END'))].decode('utf-8')
					break;

			receiver = Receiver(conn, addr, feedID)
			receiver.start()



class Receiver(Thread):
	def __init__(self, conn, addr, feedID):
		Thread.__init__(self)

		self.conn = conn
		self.addr = addr
		self.feedID = feedID

		print("Thread ready:", str(self.addr[0]) +":"+str(self.addr[1])+":"+str(self.feedID))

	def run(self):
		while self.conn is not None:
			data = b''
			while True:
				data += self.conn.recv(1024)

				if b'END' in data:
					data = data[:len(data)-len('END')]
					break

			print(self.feedID, "Received:", len(data))

if __name__ == '__main__':
	receivePortListener = Listener(('localhost', 5000))
	receivePortListener.start()



	#respondPortListener = Listener(('localhost', 5001))
	#respondPortListener.start()
