class Trade:

	def __init__(self, create_date, ticker, entry_date, exit_date, shares, exit, entry, stop_loss, actual_exit_price, actual_entry_price, status, order_id):
		self.shares = shares
		self.planned_exit_price = exit
		self.planned_entry_price = entry
		self.create_date = create_date
		self.entry_date = entry
		self.exit_date = exit_date
		self.stop_loss = stop_loss
		self.actual_exit_price = actual_exit_price
		self.actual_entry_price = actual_entry_price	
		self.status=status
		self.ticker=ticker
		self.order_id=order_id