# Ben Ryan C15507277

import os
import sys
import unittest

path = os.getcwd().split('\\')
path = '\\'.join(path[:len(path) - 1])
sys.path.append(path + '\\CommonFiles')
sys.path.append(path + '\\Client\\src')
sys.path.append(path + '\\Server\\src')

import alertTests
import blobTests
import cannyTests
import harrisTests
import modelTests
import motionTests
import ridgeTests
import sobelTests


if __name__ == '__main__':
	if len(sys.argv) == 2:
		mode = sys.argv[1]

		if mode == 'motion':
			motionTests.run()
		elif mode == 'CNN':
			modelTests.run()
		elif mode == 'alertSystem':
			alertTests.run()
		elif mode == 'blob':
			blobTests.run()
		elif mode == 'canny':
			cannyTests.run()
		elif mode == 'harris':
			harrisTests.run()
		elif mode == 'ridge':
			ridgeTests.run()
		elif mode == 'sobel':
			sobelTests.run()
		elif mode == 'help':
			print("Usage: \'python tester.py <mode>\'")
			print("\n\nModes: motion, CNN, alertSystem\nblob, canny, harris, ridge, sobel")
	else:
		print("Usage: \'python tester.py <mode>\'")
		print("\n\nModes: motion, CNN, alertSystem\nblob, canny, harris, ridge, sobel")
