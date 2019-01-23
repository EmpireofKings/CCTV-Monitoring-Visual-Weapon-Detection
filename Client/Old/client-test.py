import cv2
import numpy
import socket
import _pickle as pickle

image = cv2.imread("./Test-Data/butterfly.png")
cv2.imshow("image", image)
cv2.waitKey(0)

serial = pickle.dumps(image)

length = len(serial)

print("Serial Length: ", length)

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect(('35.204.94.151', 5000))

sentTotal = 0

while sentTotal < length:
	sentAmt = socket.send(serial[sentTotal:])
	sentTotal += sentAmt

print("sent")

received = 0
data = b''
length = 57767
while received < length:
	data += socket.recv(length)
	received = len(data)

image = pickle.loads(data)
cv2.imshow("image", image)
cv2.waitKey(0)
