class Bar:
	def __init__(self, data):
		self.time = data['t']
		self.open = data['o']
		self.high = data['h']
		self.low= data['l']
		self.close = data['c']
		self.volume = data['v']