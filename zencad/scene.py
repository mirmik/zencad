# class ViewShape:
# 	def __init__(self, shape, color):
# 		self.shape = shape
# 		self.color = color

# class Scene:
# 	def __init__(self):
# 		self.array = []

# 	def add(self, shape, color = (0.46, 0.46, 0.46)):
# 		self.array.append(ViewShape(shape, color))

# 	def init_viewer(self):
# 		scn = pyservoce.Scene()

# 		for vs in self.array:
# 			scn.add(vs.shape.unlazy(), pyservoce.Color(*vs.color))

# 		self.viewer = pyservoce.Viewer(scn)