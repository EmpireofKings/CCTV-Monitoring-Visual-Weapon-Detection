from collections import deque
import time

d = deque(maxlen=10)

for i in range(100):
	d.append(i)
	time.sleep(1)
	print(d)