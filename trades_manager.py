import logging
import trades_db
import bot_configuration
import time

def expire_trades(brokerage):
	logging.info('Expiring trades...')

def handle_open_buy_orders(brokerage):
	logging.info('Handling open buy orders...')

def handle_open_sell_orders(brokerage):
	logging.info('Handling open sell orders...')

#Step 3
def handle_open_trades(brokerage):
	logging.info('Handling open trades...')
	trades = trades_db.get_open_trades()

	# Get all open trades in the db, oldest first.
	for trade in trades:
		# Always sync them with the position in the brokerage account.
		synced_trade = None
		position = brokerage.get_position(trade.ticker)

		# Should never happen, but if it does and we have no position for a trade, mark it as invalid.
		if (position == None):
			logging.info(f'Missing position for {trade.create_date}. Marking as invalid...')
			trades_db.invalidate(trade.create_date)
		# Otherwise, sync.
		else:
			trades_db.sync(trade.create_date, position)
			synced_trade = trades_db.get(trade.create_date)

		# Sell if stop loss hit or update trailing stop loss.
		if synced_trade is not None:
			bar = brokerage.get_bar(trade.ticker)
			logging.debug(f'{trade.ticker}: planned_exit_price: {trade.planned_exit_price}, current_price: {bar.close}.')

			# If it's less than the stop loss, we issue a sell order and mark the trade as selling.
			if bar.close <= trade.stop_loss:
				logging.debug(f'{trade.ticker}: Selling {trade.ticker} at {bar.close} due to passing stop loss {trade.stop_loss}...')
				if brokerage.sell(trade, bar.close) == True:
					trades_db.sell(trade.create_date)

			# If it's over the planned exit price, we adjust the trailing stop loss.
			if bar.close >= trade.planned_exit_price:
				percentage_difference = (bar.close - trade.planned_exit_price) / trade.planned_exit_price
				if percentage_difference < bot_configuration.TRAILING_STOP_LOSS:
					logging.debug(f'{trade.ticker}: Planned exit price of {trade.planned_exit_price} exceeded to {bar.close}. Updating stop loss to {bar.close}...')
					trades_db.update_stop_loss(trade.create_date, bar.close)
				else:
					new_stop_loss = bar.close - (bar.close * bot_configuration.TRAILING_STOP_LOSS)
					logging.debug(f'{trade.ticker}: Planned exit price of {trade.planned_exit_price} exceeded to {bar.close}. Updating stop loss to {new_stop_loss}...')
					trades_db.update_stop_loss(trade.create_date, new_stop_loss)

#Step 4
def open_new_trades(brokerage):
	logging.info('Opening new trades...')
	# Checking to see how many open, buying or selling trades we have after all the other steps finished.
	open_trades = trades_db.get_active_trades()

	# If we hit the max, do nothing.
	if (len(open_trades) >= bot_configuration.MAX_TRADES_OPEN):
		return

	# Counter for tracking how many trade slots we have to fill.
	trades_to_open = bot_configuration.MAX_TRADES_OPEN - len(open_trades)
	queued_trades = trades_db.get_queued_trades()

	# Createa closure around the buy logic so we can get a boolean
	def buy_closure(trade):
		if trade.create_date + (60.0 * 60.0 * 24.0 * 7.0) >= time.time():
			trades_db.expire(trade.create_date)
		else:
			bar = brokerage.get_bar(trade.ticker)

			if bar.close <= trade.planned_entry_price:
				logging.debug(f'{trade.ticker}: Planned entry price of {trade.planned_exit_price} exceeded to {bar.close}. Buying shares...')
				if brokerage.buy(trade) == True:
					trades_db.buy(trade.create_date)
					return True

		return False

	# Get all queued trades in database
	for trade in queued_trades:
		if trades_to_open <= 0:
			break;


		if buy_closure(trade) == True:
			trades_to_open -= 1

