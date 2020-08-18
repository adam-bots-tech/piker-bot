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

	# Return order id or None if failed
	def sell(self, trade, sell_price):
		return True

	# Return order id or None if failed
	def buy(self, trade, buy_price):
		return True

	# Return Order object or None if 404
	def get_order(self, order_id):
		return Order('ab341235abe2341', 'new', 500.0, 15)