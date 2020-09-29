import logging
import bot_configuration
from datetime import datetime
from datetime import timedelta
import math
import technical_analysis as ta
import json

# Pre-workflow: Check to see if the user has added new trades to the trade journal
def pull_queued_trades(journal, trades_db):
	journal.bootstrap()
	rows = journal.get_queued_trades()
	header_row = rows[0]

	for row in rows:
		#We don't want to create a trade from the header row or empty rows at the end of the rows list.
		if row[0] == '' or row[0].lower() == 'ticker':
			continue

		trade = trades_db.create_new_long_trade(row[0], row[2], row[3], row[4], row[6], row[8])
		journal.create_trade_record(trade, row[5], row[7])
		logging.critical(f'Trade added to Queue: [{row[0]}, long, {row[2]}, {row[3]}, {row[4]}]')

	journal.reset_queued_trades(header_row)

# Step one: Expire any expired queued trades in the database, so we don't run them in later steps.
def expire_trades(trades_db):
	trades=trades_db.get_queued_trades()

	for trade in trades:
		days = 1 if trade.expiration_date < 1 else trade.expiration_date

		expiration_date = datetime.fromtimestamp(trade.create_date) + timedelta(days=trade.expiration_date)

		if datetime.timestamp(datetime.now()) >= datetime.timestamp(expiration_date):
			logging.critical(f'{trade.ticker}: Queued Trade {trade.create_date} expired.')
			trades_db.expire(trade)

# Step two: Update the database and trade journal for trades with open buy orders
def handle_open_buy_orders(brokerage, journal, trades_db):
	trades = trades_db.get_trades_being_bought()

	for trade in trades:
		order = brokerage.get_order(trade.buy_order_id)

		if order is None:
			logging.error(f'Brokerage API failed to return an order. (Order ID: {trade.buy_order_id})')
			continue

		# Remove the price record from the state database and mark the purchase as complete based on status
		if order.status == 'canceled':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} canceled. (Order ID: {order.order_id})')
			trade = trades_db.cancel(trade)
			journal.update_trade_record(trade)
		elif order.status == 'expired':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} expired. (Order ID: {order.order_id})')
			trade = trades_db.expire(trade)
			journal.update_trade_record(trade)
		elif order.status == 'filled':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} filled at {order.sale_price}. (Order ID: {order.order_id})')
			trade = trades_db.open(trade, order.shares, order.sale_price)
			journal.update_trade_record(trade, buy_metadata=json.dumps(ta.analyze(trade.ticker, brokerage)))
		elif order.status == 'replaced':
			logging.critical(f'{trade.ticker}: Trade buy order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trade = trades_db.replace_buy(trade, order.replacement_order_id)
			journal.update_trade_record(trade)

# Step three: Update the database and trade journal for trades with open sell orders
def handle_open_sell_orders(brokerage, journal, trades_db):
	trades = trades_db.get_trades_being_sold()

	for trade in trades:
		order = brokerage.get_order(trade.sell_order_id)

		if order is None:
			logging.error(f'Brokerage API failed to return an order. (Order ID: {trade.sell_order_id})')
			continue

		# Remove the price record from the state database and mark the sale as complete based on status
		if order.status == 'canceled':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} canceled. (Order ID: {order.order_id})')
			trade = trades_db.cancel_sale(trade)
			journal.update_trade_record(trade)
		elif order.status == 'expired':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} expired. (Order ID: {order.order_id})')
			trade = trades_db.expire_sale(trade)
			journal.update_trade_record(trade)
		elif order.status == 'filled':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} filled at {order.sale_price}. (Order ID: {order.order_id})')
			trade = trades_db.close(trade, order.sale_price)
			journal.update_trade_record(trade, sale_metadata=json.dumps(ta.analyze(trade.ticker, brokerage)))
		elif order.status == 'replaced':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trade = trades_db.replace_sale(trade, order.replacement_order_id)
			journal.update_trade_record(trade)

# Step four: Check the status on positions we already have and sell if the correct conditions have been met.
def handle_open_trades(brokerage, stock_math, journal, trades_db):
	trades = trades_db.get_open_long_trades()

	for trade in trades:

		now = datetime.utcnow()

		# Sell within last 30 minutes if marked for sale at end of the day
		if now.hour >= 19 and now.minute >= 30:
			if trade.sell_at_end_day == 1:
				logging.critical(f'{trade.ticker}: Trade is flagged for a sale at end of the day. Selling {trade.shares} shares at {now.hour}:{now.minute}...')
				sell(brokerage, trades_db, trade, journal)
				continue

		bars = brokerage.get_last_bars(trade.ticker, 10, 'minute')

		if (bars == None):
			logging.error('Brokerage API failed to return last three chart bars.')
			continue

		sma3 = stock_math.sma_3_close(bars)
		rsi10 = stock_math.rsi_10_close(bars)
		bar = bars[0]

		logging.info(f'{trade.ticker}: OPEN PRICE {bar.close} SMA3 {sma3} RSI10 {rsi10} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {trade.stop_loss}')

		# If the sma3 is less than or equal to the stop loss, we sell.
		if sma3 <= trade.stop_loss:
			logging.critical(f'{trade.ticker}: STOP {trade.stop_loss} exceeded by SMA3 {sma3}. Selling {trade.shares} shares...')
			sell(brokerage, trades_db, trade, journal)
			continue

		#Once the price passes above within 1% of the exit price, we set a marker to sell, in case the price immediately drops below into a downward trend
		if bar.close >= trade.planned_exit_price - (trade.planned_exit_price * 0.01):
			trades_db.set_sale_price_marker(trade.ticker, trade.id)

		sale_triggered = trades_db.get_sale_price_marker(trade.ticker, trade.id)

		# We only sell if the price is less than the sma3 and therefore, in a downward trend OR has an RSI over 70, showing it's overbought. 
		if sale_triggered:

			if sma3 < bar.close or rsi10 > 70.0:

				if rsi10 > 70.0:
					logging.critical(f'{trade.ticker}: RSI {rsi10} is over 70. Stock is overbought. Selling {trade.shares} shares at {bar.close}...')
				else:
					logging.critical(f'{trade.ticker}: PRICE {bar.close} less than SMA3 {sma3} with RSI {rsi10}. Trend has shifted. Selling {trade.shares} shares...')

				sell(brokerage, trades_db, trade, journal)
			else:
				logging.critical(f'{trade.ticker} exceeded the EXIT {trade.planned_exit_price}, but still in upward trend... (PRICE {bar.close}) (RSI {rsi10})')

# Step five: If we are able to open new trades for the day, check the status on tickers for trades in the queue and purchase shares if the correct conditions have been met.
def open_new_trades(brokerage, stock_math, journal, trades_db):
	queued_trades = trades_db.get_queued_long_trades()

	for trade in queued_trades:
		now = datetime.utcnow()

		# Prohibit the purchase of shares in the last hour if a trade is marked for sale at the end of the day
		if now.hour >= 19:
			if trade.sell_at_end_day == 1:
				logging.critical(f'{trade.ticker} cannot be purchased. Trade is flagged for sale at end of day and it is now past 3:00pm.')
				continue

		bars = brokerage.get_last_bars(trade.ticker, 10, 'minute')

		if (bars == None):
			logging.error('Brokerage API failed to return last three chart bars.')
			continue

		sma5 = stock_math.sma_5_close(bars)
		rsi10 = stock_math.rsi_10_close(bars)
		bar = bars[0]

		logging.info(f'{trade.ticker}: QUEUED PRICE {bar.close} SMA5 {sma5} RSI10 {rsi10} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {trade.stop_loss}')

		# Setting a marker that the price has moved into the entry range in case it immediately reverses trend.
		if bar.close > trade.stop_loss and bar.close <= trade.planned_entry_price:
			trades_db.set_buy_price_marker(trade.ticker, trade.id)

		buy_triggered = trades_db.get_buy_price_marker(trade.ticker, trade.id)

		# Only buy if the price has fallen below the planned entry price on a previous tick, but has moved above the stop loss, sma5 and planned_entry_price with an RSI of less than 45
		if buy_triggered and bar.close > trade.stop_loss and bar.close < sma5:
			logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price}, but still in a downward trend... (PRICE {bar.close}) (RSI {rsi10})')
		elif buy_triggered and bar.close > trade.stop_loss and bar.close > sma5 and bar.close <= trade.planned_entry_price:
			logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and in an upward trend, but PRICE {bar.close} below ENTRY {trade.planned_entry_price}... (RSI {rsi10})')
		elif buy_triggered and bar.close > trade.stop_loss and bar.close > sma5 and bar.close > trade.planned_entry_price and rsi10 >= 45.0:
			logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and in upward trend, but RSI above 45... (PRICE {bar.close}) (RSI {rsi10})')
		elif buy_triggered and bar.close > trade.stop_loss and bar.close > sma5 and bar.close > trade.planned_entry_price and rsi10 < 45.0:
			logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and in an upward trend with RSI {rsi10} under 45. Executing purchase at PRICE {bar.close}....')
			buy(brokerage, trades_db, bot_configuration, trade, bar, journal)


# We refactor the buy and sell logic into smaller methods for code reuse and to make the larger functions easier to read.
# We make a clear distinction between the logic in deciding on a sale or purchase and the logic in executing the sale and purchase

def sell(brokerage, trades_db, trade, journal):
	order_id = brokerage.sell(trade.ticker, trade.shares)
	if order_id is not None:
		trade = trades_db.sell(trade, order_id)
		journal.update_trade_record(trade)
		logging.critical(f'{trade.ticker}: {trade.shares} shares sold at market price. (Order ID: {order_id})')
		return True
	else:
		logging.error('Brokerage API failed to complete sell order.')
		return False

def buy(brokerage, trades_db, bot_configuration, trade, bar, journal):
	buying_power = brokerage.get_buying_power()

	if (buying_power == None):
		logging.error('Brokerage API failed to return the account balance. Cannot complete trade.')
		return False

	if (buying_power == False):
		logging.error('Maximum number of purchases has been executed for the day. Cannot complete trade')
		return False

	if buying_power < bot_configuration.MIN_AMOUNT_PER_TRADE:
		logging.critical(f'Not enough buying power to complete trade. (Buying Power: {buying_power})')
		trade = trades_db.out_of_money(trade)
		journal.update_trade_record(trade)
		return False

	trade_amount = buying_power * bot_configuration.PERCENTAGE_OF_ACCOUNT_TO_LEVERAGE

	if trade_amount < bot_configuration.MIN_AMOUNT_PER_TRADE:
		trade_amount = bot_configuration.MIN_AMOUNT_PER_TRADE

	# Shares are dynamically calculated from a percentage of the total brokerage account
	shares = math.trunc(trade_amount / bar.close)

	order_id = brokerage.buy(trade.ticker, shares)

	if order_id is not None:
		logging.critical(f'{trade.ticker}: {shares} shares bought at market price. (Order ID: {order_id})')
		trade = trades_db.buy(trade, shares, order_id)
		journal.update_trade_record(trade)
		return True
	else:
		logging.error('Brokerage API failed to complete buy order.')

	return False
