from matplotlib import pyplot as plt
import _pickle as pickle
import os
import numpy as np

def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

data = []

paths = os.listdir(os.getcwd())

for path in paths:
	if 'performanceData' in path:
		with open(path, 'rb') as fp:
			data.append(pickle.load(fp))


colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9']
colorCount = 1

x = []
y = []
for set in data:
	avg = sum(set[0]) / len(set[0])
	x.append(colorCount)
	y.append(avg)
	colorCount += 1
	plt.figure()
	plt.plot(set[1], smooth(set[0], 20))
	plt.xlabel('Time')
	plt.ylabel('FPS')
	plt.ylim(top=30, bottom=0)


plt.figure()
plt.bar(x, y)
plt.xlabel('Feed')
plt.ylabel('Average FPS')
plt.ylim(top=30, bottom=0)

plt.show()

