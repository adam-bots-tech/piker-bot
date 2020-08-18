class Order:
	def __init__(self, order_id, status, sale_price, shares):
		self.order_id = order_id	
		#https://alpaca.markets/docs/trading-on-alpaca/orders/#order-lifecycle for a list of statuses
		self.status = status	
		self.sale_price = sale_price
		self.shares = shares
