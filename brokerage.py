class Position:
	def __init__(self, ticker, shares, price):
		self.ticker=ticker
		self.shares=shares
		self.price=price

class Bar:
	def __init__(self, data):
		self.time = data['t']
		self.open = data['o']
		self.high = data['t']
		self.low= data['t']
		self.close = data['t']
		self.volume = data['t']

def is_open():
	# IMPLEMENT ME
	return True

# Return a Position object or None if 404
def get_position(ticker):
	return Position('TSLA', 5, 500.0)

# Return a Bar object or None if 404
def get_last_bar(ticker):
	return Bar({
		"t": 1544129220,
		"o": 172.26,
		"h": 172.3,
		"l": 172.16,
		"c": 172.18,
		"v": 3892,
	})

# Return True or False based on whether or not the trade passed
def sell(trade):
	return True

# Return True or False based on whether or not the trade passed
def buy(trade):
	return True