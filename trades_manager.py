import logging
import bot_configuration
from datetime import datetime
from datetime import timedelta
import math
import technical_analysis as ta
import json
import candlestick

def expire_trades(brokerage, trades_db):
	trades=trades_db.get_queued_trades()

	# Get all the queued trades to look for expired ones
	for trade in trades:
		expiration_date = datetime.fromtimestamp(trade.create_date) + timedelta(days=trade.expiration_date)

		if datetime.timestamp(datetime.now()) >= datetime.timestamp(expiration_date):
			logging.critical(f'{trade.ticker}: Queued Trade {trade.create_date} expired.')
			trades_db.expire(trade.create_date)


def handle_open_buy_orders(brokerage, trades_db, s):
	trades = trades_db.get_trades_being_bought()

	for trade in trades:
		order = brokerage.get_order(trade.buy_order_id)

		if order is None:
			logging.error(f'Brokerage API failed to return an order. (Order ID: {trade.buy_order_id})')
			continue

		if order.status == 'canceled':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} canceled. (Order ID: {order.order_id})')
			trades_db.cancel(trade.create_date)
			prices = s.get_last_prices()
			if 'buy'+trade.ticker+str(trade.id) in prices.keys():
				del prices['buy'+trade.ticker+str(trade.id)]
			price = s.set_last_prices(prices)
		elif order.status == 'expired':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} expired. (Order ID: {order.order_id})')
			trades_db.expire(trade.create_date)
			prices = s.get_last_prices()
			if 'buy'+trade.ticker+str(trade.id) in prices.keys():
				del prices['buy'+trade.ticker+str(trade.id)]
			price = s.set_last_prices(prices)
		elif order.status == 'filled':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} filled at {order.sale_price}. (Order ID: {order.order_id})')
			trades_db.open(trade.create_date, order.shares, order.sale_price, json.dumps(ta.analyze(trade.ticker, brokerage)), candlestick.create_15_minute_base64(trade.ticker, brokerage))
			prices = s.get_last_prices()
			if 'buy'+trade.ticker+str(trade.id) in prices.keys():
				del prices['buy'+trade.ticker+str(trade.id)]
			price = s.set_last_prices(prices)
		elif order.status == 'replaced':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trades_db.replace_buy(trade.create_date, order.replacement_order_id)
			prices = s.get_last_prices()
			if 'buy'+trade.ticker+str(trade.id) in prices.keys():
				del prices['buy'+trade.ticker+str(trade.id)]
			price = s.set_last_prices(prices)


def handle_open_sell_orders(brokerage, trades_db, s):
	trades = trades_db.get_trades_being_sold()

	for trade in trades:
		order = brokerage.get_order(trade.sell_order_id)

		if order is None:
			logging.error(f'Brokerage API failed to return an order. (Order ID: {trade.sell_order_id})')
			continue

		if order.status == 'canceled':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} canceled. (Order ID: {order.order_id})')
			trades_db.cancel_sale(trade.create_date)
			prices = s.get_last_prices()
			if 'sell'+trade.ticker+str(trade.id) in prices.keys():
				del prices['sell'+trade.ticker+str(trade.id)]
			price = s.set_last_prices(prices)
		elif order.status == 'expired':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} expired. (Order ID: {order.order_id})')
			trades_db.expire_sale(trade.create_date)
			prices = s.get_last_prices()
			if 'sell'+trade.ticker+str(trade.id) in prices.keys():
				del prices['sell'+trade.ticker+str(trade.id)]
			price = s.set_last_prices(prices)
		elif order.status == 'filled':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} filled at {order.sale_price}. (Order ID: {order.order_id})')
			trades_db.close(trade.create_date, order.sale_price, json.dumps(ta.analyze(trade.ticker, brokerage)), candlestick.create_15_minute_base64(trade.ticker, brokerage))
			prices = s.get_last_prices()
			if 'sell'+trade.ticker+str(trade.id) in prices.keys():
				del prices['sell'+trade.ticker+str(trade.id)]
			price = s.set_last_prices(prices)
		elif order.status == 'replaced':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trades_db.replace_sale(trade.create_date, order.replacement_order_id)
			prices = s.get_last_prices()
			if 'sell'+trade.ticker+str(trade.id) in prices.keys():
				del prices['sell'+trade.ticker+str(trade.id)]
			price = s.set_last_prices(prices)

#Step 3
def handle_open_trades(brokerage, trades_db, s):
	trades = trades_db.get_open_long_trades()

	# Get all open trades in the db, oldest first.
	for trade in trades:

		bars = brokerage.get_last_three_bars(trade.ticker)

		if (bars == None):
			logging.error('Brokerage API failed to return last three chart bars.')
			continue

		three_bar_avg = 0.0

		for bar in bars:
			three_bar_avg += bar.close

		three_bar_avg = three_bar_avg / 3

		bar = bars[0]

		logging.debug(f'{trade.ticker}: PRICE {bar.close} TRIPLE AVERAGE {three_bar_avg} ENTRY {trade.planned_min_entry_price}-{trade.planned_max_entry_price} EXIT {trade.planned_exit_price} STOP {trade.stop_loss}')

		# If the three bar avg is less than or equal to the stop loss, we sell.
		if three_bar_avg <= trade.stop_loss:
			logging.critical(f'{trade.ticker}: STOP {trade.stop_loss} exceeded by TRIPLE AVERAGE {three_bar_avg}. Selling {trade.shares} shares...')
			order_id = brokerage.sell(trade.ticker, trade.shares)
			if order_id is not None:
				trades_db.sell(trade.create_date, order_id)
				prices = s.get_last_prices()
				if trade.ticker in prices.keys():
					del prices[trade.ticker + str(trade.id)]
					s.set_last_prices(prices)
			else:
				logging.error('Brokerage API failed to complete sell order.')

		if bar.close >= trade.planned_exit_price:
			prices = s.get_last_prices()
			prices['sell'+trade.ticker+str(trade.id)] = True
			price = s.set_last_prices(prices)

		prices = s.get_last_prices()
		sale_triggered = True
		if 'sell'+trade.ticker+str(trade.id) not in prices.keys() or prices['sell'+trade.ticker+str(trade.id)] == False: 
			sale_triggered = False

		# If it's over the planned exit price, we see if the price is below the three point average. If so, a downward trend has started and we sell.
		if sale_triggered:

			if three_bar_avg < bar.close:
				logging.critical(f'{trade.ticker}: PRICE {bar.close} less than TRIPLE AVERAGE {three_bar_avg}. Trend has shifted. Selling {trade.shares} shares...')
				order_id = brokerage.sell(trade.ticker, trade.shares)
				if order_id is not None:
					trades_db.sell(trade.create_date, order_id)
					logging.critical(f'{trade.ticker}: {trade.shares} shares sold at market price. (Order ID: {order_id})')
				else:
					logging.error('Brokerage API failed to complete sell order.')
			else:
				logging.critical(f'{trade.ticker}: PRICE {bar.close} exceeded the EXIT {trade.planned_exit_price}, but still in upward trend..')

#Step 4
def open_new_trades(brokerage, trades_db, s):
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
		bars = brokerage.get_last_three_bars(trade.ticker)

		if (bars == None):
			logging.error('Brokerage API failed to return last three chart bars.')
			return False

		three_bar_avg = 0.0

		for bar in bars:
			three_bar_avg += bar.close

		three_bar_avg = three_bar_avg / 3

		bar = bars[0]

		logging.debug(f'{trade.ticker}: PRICE {bar.close} TRIPLE AVERAGE {three_bar_avg} ENTRY {trade.planned_min_entry_price}-{trade.planned_max_entry_price} EXIT {trade.planned_exit_price} STOP {trade.stop_loss}')

		if bar.close >= trade.planned_min_entry_price and bar.close <= trade.planned_max_entry_price:
			prices = s.get_last_prices()
			prices['buy'+trade.ticker+str(trade.id)] = True
			price = s.set_last_prices(prices)

		prices = s.get_last_prices()
		buy_triggered = True
		if 'buy'+trade.ticker+str(trade.id) not in prices.keys() or prices['buy'+trade.ticker+str(trade.id)] == False: 
			buy_triggered = False

		if buy_triggered and bar.close > trade.stop_loss and bar.close < three_bar_avg:
			logging.critical(f'{trade.ticker} {bar.close} in between ENTRY {trade.planned_min_entry_price}-{trade.planned_max_entry_price}, but still in a downward trend...')
		elif buy_triggered and bar.close < trade.stop_loss and bar.close < three_bar_avg:
			logging.critical(f'{trade.ticker} {bar.close} in between ENTRY {trade.planned_min_entry_price}-{trade.planned_max_entry_price} and below STOP LOSS {trade.stop_loss}. Cancelling trade...')
			trades_db.stop_loss(trade.create_date)
		# Only buy if the price is below the planned entry price, but above the stop loss and above the triple average
		elif buy_triggered and bar.close > trade.stop_loss and bar.close > three_bar_avg:
			buying_power = brokerage.get_buying_power()
			logging.debug(f'{trade.ticker} PRICE {bar.close} in between ENTRY {trade.planned_min_entry_price}-{trade.planned_max_entry_price} and in an upward trend. Executing buy for {trade.shares} shares....')

			if (buying_power == None):
				logging.error('Brokerage API failed to return the account balance. Cannot complete trade.')
				return False

			if buying_power < bot_configuration.MIN_AMOUNT_PER_TRADE:
				logging.critical(f'Not enough buying power to complete trade. (Buying Power: {buying_power})')
				trades_db.out_of_money(trade.create_date)
				return False

			trade_amount = buying_power * bot_configuration.PERCENTAGE_OF_ACCOUNT_TO_LEVERAGE

			if trade_amount < bot_configuration.MIN_AMOUNT_PER_TRADE:
				trade_amount = bot_configuration.MIN_AMOUNT_PER_TRADE

			shares = math.trunc(trade_amount / bar.close)

			logging.debug(f'Dynamic Shares: SHARES {shares} TRADE AMOUNT {trade_amount} BUYING POWER {buying_power}')

			order_id = brokerage.buy(trade.ticker, shares)

			if order_id is not None:
				logging.critical(f'{trade.ticker}: {shares} shares bought at market price. (Order ID: {order_id})')
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

