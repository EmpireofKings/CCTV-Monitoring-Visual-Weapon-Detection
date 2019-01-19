imageSize = (100,100)
imageShape = (imageSize[0], imageSize[1], 3)
displaySize = (640, 640)
batchSize = 64



DEMO_MODE = False

def activateDemoMode():
	ans = input("Enable Demo Mode? (Y/N)")
	
	if ans == 'y' or ans == 'Y':
		print("Demo mode enabled. Press any key to progress frame by frame")
		return True
	else:
		return False
	