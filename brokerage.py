import bar
import position

class Brokerage:

	def is_open(self):
		# IMPLEMENT ME
		return True

	# Return a Position object or None if 404
	def get_position(self, ticker):
		return Position('TSLA', 5, 500.0)

	# Return a Bar object or None if 404
	def get_last_bar(self, ticker):
		return Bar({
			"t": 1544129220,
			"o": 172.26,
			"h": 172.3,
			"l": 172.16,
			"c": 172.18,
			"v": 3892,
		})

	# Return True or False based on whether or not the trade passed
	def sell(self, trade, sell_price):
		return True

	# Return True or False based on whether or not the trade passed
	def buy(self, trade, buy_price):
		return True