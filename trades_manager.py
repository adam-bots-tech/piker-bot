import logging
import bot_configuration
from datetime import datetime
from datetime import timedelta
import math
import technical_analysis as ta
import json

def pull_queued_trades(trades_db, journal):
	journal.bootstrap()
	rows = journal.get_queued_trades()
	header_row = rows[0]

	for row in rows:
		if row[0] == '' or row[0].lower() == 'ticker':
			continue

		trade = trades_db.create_new_long_trade(row[0], row[2], row[3], row[4], row[6], row[8])
		journal.create_trade_record(trade, row[5], row[7])
		logging.critical(f'Trade added to Queue: [{row[0]}, long, {row[2]}, {row[3]}, {row[4]}]')

	journal.reset_queued_trades(header_row)

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

		# Remove the price record from the state database and mark the purchase as complete based on status
		if order.status == 'canceled':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} canceled. (Order ID: {order.order_id})')
			trades_db.cancel(trade.create_date)
			s.remove_buy_price_marker(trade.ticker, trade.id)
		elif order.status == 'expired':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} expired. (Order ID: {order.order_id})')
			trades_db.expire(trade.create_date)
			s.remove_buy_price_marker(trade.ticker, trade.id)
		elif order.status == 'filled':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} filled at {order.sale_price}. (Order ID: {order.order_id})')
			trades_db.open(trade.create_date, order.shares, order.sale_price, json.dumps(ta.analyze(trade.ticker, brokerage)))
			s.remove_buy_price_marker(trade.ticker, trade.id)
		elif order.status == 'replaced':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trades_db.replace_buy(trade.create_date, order.replacement_order_id)
			s.remove_buy_price_marker(trade.ticker, trade.id)


def handle_open_sell_orders(brokerage, trades_db, s):
	trades = trades_db.get_trades_being_sold()

	for trade in trades:
		order = brokerage.get_order(trade.sell_order_id)

		if order is None:
			logging.error(f'Brokerage API failed to return an order. (Order ID: {trade.sell_order_id})')
			continue

		# Remove the price record from the state database and mark the sale as complete based on status
		if order.status == 'canceled':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} canceled. (Order ID: {order.order_id})')
			trades_db.cancel_sale(trade.create_date)
			s.remove_sale_price_marker(trade.ticker, trade.id)
		elif order.status == 'expired':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} expired. (Order ID: {order.order_id})')
			trades_db.expire_sale(trade.create_date)
			s.remove_sale_price_marker(trade.ticker, trade.id)
		elif order.status == 'filled':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} filled at {order.sale_price}. (Order ID: {order.order_id})')
			trades_db.close(trade.create_date, order.sale_price, json.dumps(ta.analyze(trade.ticker, brokerage)))
			s.remove_sale_price_marker(trade.ticker, trade.id)
		elif order.status == 'replaced':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trades_db.replace_sale(trade.create_date, order.replacement_order_id)
			s.remove_sale_price_marker(trade.ticker, trade.id)

#Step 3
def handle_open_trades(brokerage, trades_db, s, stock_math):
	trades = trades_db.get_open_long_trades()

	# Get all open trades in the db, oldest first.
	for trade in trades:

		now = datetime.utcnow()

		if now.hour >= 15 and now.minute >= 30:
			if trade.sell_at_end_day == 1:
				logging.critical(f'{trade.ticker}: Trade is flagged for a sale at end of the day. Selling {trade.shares} shares at {now.hour()}:{now.minute()}...')

				order_id = brokerage.sell(trade.ticker, trade.shares)
				if order_id is not None:
					trades_db.sell(trade.create_date, order_id)
					logging.critical(f'{trade.ticker}: {trade.shares} shares sold at market price. (Order ID: {order_id})')
				else:
					logging.error('Brokerage API failed to complete sell order.')
				continue

		bars = brokerage.get_last_ten_bars(trade.ticker)

		if (bars == None):
			logging.error('Brokerage API failed to return last three chart bars.')
			continue

		sma3 = stock_math.sma_3_close(bars)
		rsi10 = stock_math.rsi_10_close(bars)
		bar = bars[0]

		logging.debug(f'{trade.ticker}: OPEN PRICE {bar.close} TRIPLE AVERAGE {sma3} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {trade.stop_loss}')

		# If the sma3 is less than or equal to the stop loss, we sell.
		if sma3 <= trade.stop_loss:
			logging.critical(f'{trade.ticker}: STOP {trade.stop_loss} exceeded by TRIPLE AVERAGE {sma3}. Selling {trade.shares} shares...')
			order_id = brokerage.sell(trade.ticker, trade.shares)
			if order_id is not None:
				trades_db.sell(trade.create_date, order_id)
				s.remove_sale_price_marker(trade.ticker, trade.id)
			else:
				logging.error('Brokerage API failed to complete sell order.')

		#Once the price passes above the exit price, we set a marker to sell, in case the price immediately drops below into a downward trend
		if bar.close >= trade.planned_exit_price:
			s.set_sale_price_marker(trade.ticker, trade.id)

		sale_triggered = s.get_sale_price_marker(trade.ticker, trade.id)

		# We only sell if the price is less than the sma3 and therefore, in a downward trend. 
		if sale_triggered:

			if (sma3 < bar.close and rsi10 > 60.0) or rsi10 > 70.0:
				if rsi10 > 70.0:
					logging.critical(f'{trade.ticker}: RSI {rsi10} is over 70. Stock is oversold. Selling {trade.shares} shares at {bar.close}...')
				else:
					logging.critical(f'{trade.ticker}: PRICE {bar.close} less than TRIPLE AVERAGE {sma3} and RSI {rsi10}. Trend has shifted. Selling {trade.shares} shares...')
				order_id = brokerage.sell(trade.ticker, trade.shares)
				if order_id is not None:
					trades_db.sell(trade.create_date, order_id)
					logging.critical(f'{trade.ticker}: {trade.shares} shares sold at market price. (Order ID: {order_id})')
				else:
					logging.error('Brokerage API failed to complete sell order.')
			else:
				logging.critical(f'{trade.ticker} exceeded the EXIT {trade.planned_exit_price}, but still in upward trend... (PRICE {bar.close}) (RSI {rsi10})')

#Step 4
def open_new_trades(brokerage, trades_db, s, stock_math):
	queued_trades = trades_db.get_queued_long_trades()

	# Createa closure around the buy logic so we can get a boolean
	def buy_closure(trade, trades_db):
		bars = brokerage.get_last_ten_bars(trade.ticker)

		if (bars == None):
			logging.error('Brokerage API failed to return last three chart bars.')
			return False

		sma3 = stock_math.sma_3_close(bars)
		rsi10 = stock_math.rsi_10_close(bars)
		bar = bars[0]

		logging.debug(f'{trade.ticker}: QUEUED PRICE {bar.close} SMA3 {sma3} RSI10 {rsi10} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {trade.stop_loss}')

		# Setting a marker that the price has moved into the entry range in case it immediately reverses trend.
		if bar.close > trade.stop_loss and bar.close <= trade.planned_entry_price:
			s.set_buy_price_marker(trade.ticker, trade.id)

		buy_triggered = s.get_buy_price_marker(trade.ticker, trade.id)

		if buy_triggered and bar.close > trade.stop_loss and bar.close < sma3:
			logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price}, but still in a downward trend... (PRICE {bar.close}) (RSI {rsi10})')
		elif buy_triggered and bar.close < trade.stop_loss and bar.close < sma3:
			logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price}, but PRICE {bar.close} below STOP LOSS {trade.stop_loss}. Cancelling trade...')
			trades_db.stop_loss(trade.create_date)
		# Only buy if the price has fallen below the planned entry price on a previous tick, but has moved above the stop loss, sma3 and planned_entry_price
		elif buy_triggered and bar.close > trade.stop_loss and bar.close > sma3 and bar.close > trade.planned_entry_price:

			if rsi10 >= 40.0:
				logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and in upward trend, but RSI above 40... (PRICE {bar.close}) (RSI {rsi10})')
				return False

			buying_power = brokerage.get_buying_power()

			if (buying_power == None):
				logging.error('Brokerage API failed to return the account balance. Cannot complete trade.')
				return False

			if (buying_power == False):
				logging.error('Maximum number of purchases has been executed for the day. Cannot complete trade')
				return False

			if buying_power < bot_configuration.MIN_AMOUNT_PER_TRADE:
				logging.critical(f'Not enough buying power to complete trade. (Buying Power: {buying_power})')
				trades_db.out_of_money(trade.create_date)
				return False

			trade_amount = buying_power * bot_configuration.PERCENTAGE_OF_ACCOUNT_TO_LEVERAGE

			if trade_amount < bot_configuration.MIN_AMOUNT_PER_TRADE:
				trade_amount = bot_configuration.MIN_AMOUNT_PER_TRADE

			# Shares are dynamically calculated from a percentage of the total brokerage account
			shares = math.trunc(trade_amount / bar.close)
			logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and in an upward trend with RSI {rsi10} over 40. Executing buy for {trade.shares} shares at PRICE {bar.close}....')

			order_id = brokerage.buy(trade.ticker, shares)

			if order_id is not None:
				logging.critical(f'{trade.ticker}: {shares} shares bought at market price. (Order ID: {order_id})')
				trades_db.buy(trade.create_date, shares, order_id)
				s.remove_buy_price_marker(trade.ticker, trade.id)
				return True
			else:
				logging.error('Brokerage API failed to complete buy order.')
		
		return False

	# Get all queued trades in database
	for trade in queued_trades:
		buy_closure(trade, trades_db)