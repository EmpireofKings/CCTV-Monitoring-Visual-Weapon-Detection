from collections import deque


class ResultsHandler():
	def __init__(self, amount, size):

		self.buffers = []
		for _ in range(amount):
			buf = self.ResultBuffer(size)
			self.buffers.append(buf)

	def getAverages(self):
		averages = []
		for buf in self.buffers:
			avg = buf.getAvg()
			averages.append(avg)

		return averages

	def getLengths(self):
		lengths = []
		for buf in self.buffers:
			l = len(buf)
			lengths.append(l)

		return lengths

	def __len__(self):
		return len(self.buffers)

	def append(self, results):
		for count in range(len(self.buffers)):
			buffer = self.buffers[count]
			resultSet = results[count]

			buffer.append(resultSet[0], resultSet[1])

	def assess(self):
		averages = self.getAverages()

		for avg in averages:
			if max(avg) > 0.95:
				return True

	class ResultBuffer():
		def __init__(self, size):
			self.knifeBuffer = deque(maxlen=size)
			self.pistolBuffer = deque(maxlen=size)

		def getAvg(self):
			knifeAvg = sum(self.knifeBuffer) / len(self.knifeBuffer)
			pistolAvg = sum(self.pistolBuffer) / len(self.pistolBuffer)

			return (knifeAvg, pistolAvg)

		def __len__(self):
			length = len(self.knifeBuffer)
			if length == len(self.pistolBuffer):
				return length
			else:
				return -1

		def append(self, knife, pistol):
			self.knifeBuffer.append(knife)
			self.pistolBuffer.append(pistol)
