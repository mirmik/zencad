class nqueue:
	def __init__(self):
		self.arr = [0]*10
		self.size = 5

	def add(self, obj):
		for i in range(self.size):
			self.arr[i+1] = self.arr[i]
			self.arr[0] = obj