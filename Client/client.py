# Ben Ryan - C15507277 Final Year Project
# This is the client application that will pass the frames to be processed to the server.

# Steps
#	Get video feed
#	Connect sockets to server
#	Start threads and pass in relevent data
#	Read from video source
#	Send to server
#	Receive Processed frame
#	Display/Store frame

import numpy as np
import cv2
import clientServer as cs
from threading import Thread
import easygui
import time
import sharedParams as sp

start = 0
WORKING = False
LOADING = True
processed = cs.queue.Queue()
loaded = cs.queue.Queue()

#main function on main thread
def main():
	PrintThread = Thread(target=cs.displayMessages, name="PrintThread")
	PrintThread.start()

	global WORKING
	while WORKING == False:
		WORKING = True
		vidFeed = getFeed()
		sp.DEMO_MODE = sp.activateDemoMode()
	
		if vidFeed is None:
			cs.messages.put("Error reading video feed")
			return
		
		#get video fps so we know how to encode the processed video
		vidFPS = vidFeed.get(cv2.CAP_PROP_FPS)
		
		cs.messages.put("Video feed acquired")
		
		try:
			#connect to up and down streams
			sendSocket = connectSocket(cs.HOST, cs.upStreamPort)
			readSocket = connectSocket(cs.HOST, cs.downStreamPort)
			cs.messages.put("Sockets connected")
			
			#begin threads
			LoadThread = Thread(target=loadThreadMain, name="LoadThread", args=[vidFeed])
			SendThread = Thread(target=sendThreadMain, name="SendThread",args=[sendSocket])
			ReceiveThread = Thread(target=receiveThreadMain, name="ReceiveThread", args=[readSocket])
			SaveThread = Thread(target=saveThreadMain, name="SaveThread", args=[vidFPS])
			#ReportingThread = Thread(target=reporting, name="ReportingThread")
			
			#ReportingThread.start()
			LoadThread.start()
			SendThread.start()
			ReceiveThread.start()
			SaveThread.start()
			
			cs.messages.put("Threads running")
			WORKING = True
		
			#wait for threads to stop working, then loop at start again with new feed
			while WORKING == True: True
			cs.messages.put("Threads stopped")
		
		except(ConnectionResetError,ConnectionRefusedError) as e:
			cs.messages.put(e)

#TODO
#def reporting():
	#global loaded, processed
	
	#while True:
	#	cs.messages.put("Loaded Size:" + str(loaded.qsize()))
	#	cs.messages.put("Processed Size:" + str(processed.qsize()))
	
#main function on thread for loading frames from video source	
def loadThreadMain(feed):
	global loaded, start
	
	LOADING = True
		
	start = time.time()
	while feed.isOpened():
		check, frame = feed.read()
		
		if check == True:
			#resize before sending
			frame = cv2.resize(frame, sp.imageSize)
			
			loaded.put(frame)
		else:
			LOADING = False
			feed.release()
			break
			
#main functon on thread for sending frames to server	
def sendThreadMain(socket):
	global start, loaded
	frame = initCommsUp(socket)
	
	while LOADING == True:
		cs.sendFrame(frame, socket)
		
		while loaded.empty() == True and LOADING == True : True
		
		frame = loaded.get()
			
	cs.sendMessage(cs.COMPLETE, socket)
	
#main function on thread for receiving processed frames
def receiveThreadMain(socket):
	global WORKING, start

	cs.expectedSize = int(initCommsDown(socket))	
	frameCount = 0
	
	while WORKING == True:
		frame, socket = cs.recvFrame(socket)
		frameCount +=1
				
		if frame is cs.COMPLETE:
			WORKING == False
			break
			
		processed.put(frame)

#main function on thread for saving/showing processed frames
def saveThreadMain(vidFPS):
	global processed
	
	#setup video encoder
	if sp.DEMO_MODE == False:
		fourcc = cv2.VideoWriter_fourcc(*'mp4v')
		outStream = cv2.VideoWriter('./processed.mp4', fourcc, fps=vidFPS, frameSize=sp.displaySize)
	
	frameCount = 0
	while WORKING == True:
		while processed.empty() == True : True
		
		frame = processed.get()
		frameCount +=1

		if sp.DEMO_MODE == True:
			cs.showFrame("Frame", frame, True, 0)
		else:
			outStream.write(frame)

			#if saving video break after 1000 frames
			if frameCount == 1000:
				outStream.release()
				cs.messages.put("TIME: ", time.time()-start)
				cs.messages.put("RELEASED")
				break
		
	outStream.release()
			
#used by receiveThread
def initCommsDown(socket):
	msg, _ = cs.recvMessage(socket)
	
	if msg == cs.NOTREADY:
		return
	
	cs.sendMessage(cs.READY, socket)
	
	return msg


#used by sendThread
def initCommsUp(socket):
	while loaded.empty() == True : True
	
	frame = loaded.get()
	
	if frame is not None:
		frameSerial = cs.pickle.dumps(frame)
		# _, frameSerial = cv2.imencode('.jpg', frame)
		length = len(frameSerial)
		cs.messages.put("Length " + str(length))
		cs.sendMessage(length, socket)
		resp, _ = cs.recvMessage(socket)
		if resp == cs.READY:
			cs.messages.put("Upstream comms initialised")
			return frame
	
#used by main thread
def connectSocket(HOST,PORT):
	socket = cs.sock.socket(cs.sock.AF_INET, cs.sock.SOCK_STREAM)
	socket.connect((HOST, PORT))
		
	return socket
	
#used by main thread
def getFeed():
	ans = input("Video or Camera?(V/C)")
	
	if ans == 'V' or ans == 'v':
		filename = easygui.fileopenbox()
		feed = cv2.VideoCapture(filename)
	elif ans == 'C' or ans == 'c':
		feed = cv2.VideoCapture(0)
	else:
		return

	return feed
	

if __name__ == '__main__':
	main()


	
