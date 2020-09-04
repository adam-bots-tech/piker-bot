import logging
import bot_configuration
from datetime import datetime
from datetime import timedelta
import math

def expire_trades(brokerage, trades_db):
	trades=trades_db.get_queued_trades()

	# Get all the queued trades to look for expired ones
	for trade in trades:
		expiration_date = datetime.fromtimestamp(trade.create_date) + timedelta(days=bot_configuration.MAX_DAYS_TO_KEEP_TRADE_QUEUED)

		if datetime.timestamp(datetime.now()) >= datetime.timestamp(expiration_date):
			logging.info(f'{trade.ticker}: Queued Trade {trade.create_date} expired.')
			trades_db.expire(trade.create_date)


def handle_open_buy_orders(brokerage, trades_db):
	trades = trades_db.get_trades_being_bought()

	for trade in trades:
		order = brokerage.get_order(trade.buy_order_id)

		if order is None:
			logging.error(f'Brokerage API failed to return an order. (Order ID: {trade.buy_order_id})')
			continue

		if order.status == 'canceled':
			logging.info(f'{trade.ticker}: Trade buy order {trade.create_date} canceled. (Order ID: {order.order_id})')
			trades_db.cancel(trade.create_date)
		elif order.status == 'expired':
			logging.info(f'{trade.ticker}: Trade buy order {trade.create_date} expired. (Order ID: {order.order_id})')
			trades_db.expire(trade.create_date)
		elif order.status == 'filled':
			logging.info(f'{trade.ticker}: Trade buy order {trade.create_date} filled. (Order ID: {order.order_id})')
			trades_db.open(trade.create_date, order.shares, order.sale_price)
		elif order.status == 'replaced':
			logging.info(f'{trade.ticker}: Trade buy order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trades_db.replace_buy(trade.create_date, order.replacement_order_id)


def handle_open_sell_orders(brokerage, trades_db):
	trades = trades_db.get_trades_being_sold()

	for trade in trades:
		order = brokerage.get_order(trade.sell_order_id)

		if order is None:
			logging.error(f'Brokerage API failed to return an order. (Order ID: {trade.sell_order_id})')
			continue

		if order.status == 'canceled':
			logging.info(f'{trade.ticker}: Trade sell order {trade.create_date} canceled. (Order ID: {order.order_id})')
			trades_db.cancel_sale(trade.create_date)
		elif order.status == 'expired':
			logging.info(f'{trade.ticker}: Trade sell order {trade.create_date} expired. (Order ID: {order.order_id})')
			trades_db.expire_sale(trade.create_date)
		elif order.status == 'filled':
			logging.info(f'{trade.ticker}: Trade sell order {trade.create_date} filled. (Order ID: {order.order_id})')
			trades_db.close(trade.create_date, order.sale_price)
		elif order.status == 'replaced':
			logging.info(f'{trade.ticker}: Trade sell order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trades_db.replace_sale(trade.create_date, order.replacement_order_id)

#Step 3
def handle_open_trades(brokerage, trades_db):
	trades = trades_db.get_open_long_trades()

	# Get all open trades in the db, oldest first.
	for trade in trades:
		# Always sync them with the position in the brokerage account.
		synced_trade = None
		position = brokerage.get_position(trade.ticker)


		# Should never happen, but if it does and we have no position for a trade, mark it as invalid.
		if position == False:
			logging.error(f'Brokerage API could not find position for {trade.ticker}. Marking as invalid...')
			trades_db.invalidate(trade.create_date)
		# Otherwise, sync.
		elif position == None:
			logging.error(f'Brokerage API failed to return position for {trade.ticker}.')
		else:
			trades_db.sync(trade.create_date, position)
			synced_trade = trades_db.get(trade.create_date)

		# Sell if stop loss hit or update trailing stop loss.
		if synced_trade is not None:
			bar = brokerage.get_last_bar(trade.ticker)

			if (bar == None):
				logging.error('Brokerage API failed to return last chart bar.')
				continue

			logging.debug(f'{trade.ticker}: PRICE {bar.close} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {trade.stop_loss}')

			# If it's less than the stop loss, we issue a sell order and mark the trade as selling.
			if bar.close <= trade.stop_loss:
				logging.info(f'{trade.ticker}: STOP {trade.stop_loss} exceeded by PRICE {bar.close}. Selling {trade.shares} shares...')
				order_id = brokerage.sell(trade.ticker, trade.shares)
				if order_id is not None:
					trades_db.sell(trade.create_date, order_id)
				else:
					logging.error('Brokerage API failed to complete sell order.')

			# If it's over the planned exit price, we adjust the trailing stop loss.
			if bar.close >= trade.planned_exit_price:
				percentage_difference = (bar.close - trade.planned_exit_price) / trade.planned_exit_price
				if percentage_difference < (bot_configuration.TRAILING_STOP_LOSS / 2):
					logging.info(f'{trade.ticker}: EXIT {trade.planned_exit_price} exceeded by PRICE {bar.close}. Setting new STOP {bar.close}...')
					trades_db.update_stop_loss(trade.create_date, bar.close)
				else:
					new_stop_loss = bar.close - (bar.close * bot_configuration.TRAILING_STOP_LOSS)
					logging.info(f'{trade.ticker}: EXIT {trade.planned_exit_price} exceeded by PRICE {bar.close}. Setting new STOP {new_stop_loss}...')
					trades_db.update_stop_loss(trade.create_date, new_stop_loss)

#Step 4
def open_new_trades(brokerage, trades_db):
	# Checking to see how many open, buying or selling trades we have after all the other steps finished.
	open_trades = trades_db.get_active_trades()

	# If we hit the max, do nothing.
	if (len(open_trades) >= bot_configuration.MAX_TRADES_OPEN):
		return

	# Counter for tracking how many trade slots we have to fill.
	trades_to_open = bot_configuration.MAX_TRADES_OPEN - len(open_trades)
	queued_trades = trades_db.get_queued_long_trades()

	# Createa closure around the buy logic so we can get a boolean
	def buy_closure(trade, trades_db):
		bar = brokerage.get_last_bar(trade.ticker)

		if (bar == None):
			logging.error('Brokerage API failed to return last chart bar.')
			return False

		logging.debug(f'{trade.ticker}: PRICE {bar.close} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {trade.stop_loss}')

		if bar.close <= trade.planned_entry_price and bar.close > trade.stop_loss:
			buying_power = brokerage.get_buying_power()

			if (buying_power == None):
				logging.error('Brokerage API failed to return the account balance. Cannot complete trade.')
				return False

			if buying_power < bot_configuration.MIN_AMOUNT_PER_TRADE:
				logging.warn(f'Not enough buying power to complete trade. (Buying Power: {buying_power})')
				trades_db.out_of_money(trade.create_date)
				return False

			trade_amount = buying_power * bot_configuration.PERCENTAGE_OF_ACCOUNT_TO_LEVERAGE

			if trade_amount < bot_configuration.MIN_AMOUNT_PER_TRADE:
				trade_amount = bot_configuration.MIN_AMOUNT_PER_TRADE

			shares = math.trunc(trade_amount / bar.close)

			logging.debug(f'Dynamic Shares: SHARES {shares} TRADE AMOUNT {trade_amount} BUYING POWER {buying_power}')

			order_id = brokerage.buy(trade.ticker, shares)

			if order_id is not None:
				logging.info(f'{trade.ticker}: ENTRY {trade.planned_entry_price} exceeded by PRICE {bar.close}. {shares} shares bought. (Order ID: {order_id})')
				trades_db.buy(trade.create_date, shares, order_id)
				return True
			else:
				logging.error('Brokerage API failed to complete buy order.')
		
		return False

	# Get all queued trades in database
	for trade in queued_trades:
		if trades_to_open <= 0:
			break;


		if buy_closure(trade, trades_db) == True:
			trades_to_open -= 1

