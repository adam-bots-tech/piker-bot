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

		amount = 0.0 if row[7] == '' else row[7]

		if row[1] == 'long':
			trade = trades_db.create_new_long_trade(row[0], row[2], row[3], row[4], row[6], row[8], amount)
		else:
			trade = trades_db.create_new_short_trade(row[0], row[2], row[3], row[4], row[6], row[8], amount)

		journal.create_trade_record(trade, row[5])
		logging.critical(f'Trade added to Queue: [{row[0]}, {row[1]}, {row[2]}, {row[3]}, {row[4]}]')

	journal.reset_queued_trades(header_row)

# Step one: Expire any expired queued trades in the database, so we don't run them in later steps.
def expire_trades(trades_db, journal):
	trades=trades_db.get_queued_trades()

	for trade in trades:
		days = 1 if trade.expiration_date < 1 else trade.expiration_date

		expiration_date = datetime.fromtimestamp(trade.create_date) + timedelta(days=trade.expiration_date)

		if datetime.timestamp(datetime.now()) >= datetime.timestamp(expiration_date):
			logging.critical(f'{trade.ticker}: Queued Trade {trade.create_date} expired.')
			trade = trades_db.expire(trade)
			journal.update_trade_record(trade)

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
			if trade.type == 'short':
				trade = trades_db.close(trade, order.sale_price)
			else:
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
			if trade.type == 'short':
				trade = trades_db.open(trade, order.shares, order.sale_price)
			else:
				trade = trades_db.close(trade, order.sale_price)
			journal.update_trade_record(trade, sale_metadata=json.dumps(ta.analyze(trade.ticker, brokerage)))
		elif order.status == 'replaced':
			logging.critical(f'{trade.ticker}: Trade sell order {trade.create_date} replaced. (Order ID: {order.order_id})')
			trade = trades_db.replace_sale(trade, order.replacement_order_id)
			journal.update_trade_record(trade)

# Step four: Check the status on positions we already have and sell if the correct conditions have been met.
def handle_open_trades(brokerage, stock_math, journal, trades_db):
	trades = trades_db.get_open_trades()

	for trade in trades:
		bars = brokerage.get_last_bars(trade.ticker, 10, 'minute')

		if (bars == None):
			logging.error('Brokerage API failed to return last three chart bars.')
			continue

		if trade.type == 'long':
			if is_sellable(trade, bars, stock_math, trades_db):
				sell(brokerage, trades_db, trade, journal)
		else:
			if is_short_buyable(trade, bars, stock_math, trades_db):
				buy(brokerage, trades_db, bot_configuration, trade, journal)


# Step five: If we are able to open new trades for the day, check the status on tickers for trades in the queue and purchase shares if the correct conditions have been met.
def open_new_trades(brokerage, stock_math, journal, trades_db):
	queued_trades = trades_db.get_queued_trades()

	for trade in queued_trades:
		bars = brokerage.get_last_bars(trade.ticker, 10, 'minute')

		if (bars == None):
			logging.error('Brokerage API failed to return last three chart bars.')
			continue

		if trade.type == 'long':
			if is_buyable(trade, bars, stock_math, trades_db):
				buy(brokerage, trades_db, bot_configuration, trade, journal, price=bars[0].close, amount=trade.amount)
		else:
			if is_short_sellable(trade, bars, stock_math, trades_db):
				sell(brokerage, trades_db, trade, journal, price=bars[0].close, amount=trade.amount)


# We refactor the buy and sell logic into smaller methods for code reuse and to make the larger functions easier to read.
# We make a clear distinction between the logic in deciding on a sale or purchase and the logic in executing the sale and purchase

def is_buyable(trade, bars, stock_math, trades_db):
	sma5 = stock_math.sma_5_close(bars)
	rsi10 = stock_math.rsi_10_close(bars)
	bar = bars[0]

	stop_loss = calculate_stop_loss(trade, trades_db, bar.close)

	logging.info(f'{trade.ticker}: QUEUED PRICE {bar.close} SMA5 {sma5} RSI10 {rsi10} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {stop_loss}')

	now = datetime.utcnow()

	# Prohibit the purchase of shares in the last hour if a trade is marked for sale at the end of the day
	if now.hour >= 19:
		if trade.sell_end_of_day == 1:
			logging.critical(f'{trade.ticker} cannot be purchased. Trade is flagged for sale at end of day and it is now past 3:00pm.')
			return False

	# Setting a marker that the price has moved into the entry range in case it immediately reverses trend.
	if bar.close > stop_loss and bar.close <= trade.planned_entry_price:
		trades_db.set_buy_price_marker(trade.ticker, trade.id)

	buy_triggered = trades_db.get_buy_price_marker(trade.ticker, trade.id)

	# Only buy if the price has fallen below the planned entry price on a previous tick, but has moved above the stop loss, sma5 and planned_entry_price with an RSI of less than 45
	if buy_triggered and bar.close > stop_loss and bar.close < sma5:
		logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and still in a downward trend... (PRICE {bar.close}) (RSI {rsi10})')
		return False
	elif buy_triggered and bar.close > stop_loss and bar.close > sma5 and bar.close <= trade.planned_entry_price:
		logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and in an upward trend, but PRICE {bar.close} below ENTRY {trade.planned_entry_price}... (RSI {rsi10})')
		return False
	elif buy_triggered and bar.close > stop_loss and bar.close > sma5 and bar.close > trade.planned_entry_price and rsi10 >= 45.0:
		logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and in upward trend, but RSI above 45... (PRICE {bar.close}) (RSI {rsi10})')
		return False
	elif buy_triggered and bar.close > stop_loss and bar.close > sma5 and bar.close > trade.planned_entry_price and rsi10 < 45.0:
		logging.critical(f'{trade.ticker} moved under ENTRY {trade.planned_entry_price} and in an upward trend with RSI {rsi10} under 45. Executing purchase at PRICE {bar.close}....')
		return True

	return False

def is_short_sellable(trade, bars, stock_math, trades_db):
	sma5 = stock_math.sma_5_close(bars)
	rsi10 = stock_math.rsi_10_close(bars)
	bar = bars[0]

	stop_loss = calculate_short_sale_stop_loss(trade, trades_db, bar.close)

	logging.info(f'{trade.ticker}: QUEUED PRICE {bar.close} SMA5 {sma5} RSI10 {rsi10} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {stop_loss}')

	now = datetime.utcnow()

	# Prohibit the purchase of shares in the last hour if a trade is marked for sale at the end of the day
	if now.hour >= 19:
		if trade.sell_end_of_day == 1:
			logging.critical(f'{trade.ticker} cannot be purchased. Trade is flagged for sale at end of day and it is now past 3:00pm.')
			return False

	# Setting a marker that the price has moved into the entry range in case it immediately reverses trend.
	if bar.close < stop_loss and bar.close >= trade.planned_entry_price:
		trades_db.set_buy_price_marker(trade.ticker, trade.id)

	buy_triggered = trades_db.get_buy_price_marker(trade.ticker, trade.id)

	# Only buy if the price moves above the planned entry price on a previous tick, but has moved below the stop loss, sma5 and planned_entry_price with an RSI greater than 65
	if buy_triggered and bar.close < stop_loss and bar.close > sma5:
		logging.critical(f'{trade.ticker} moved above ENTRY {trade.planned_entry_price} and still in an upward trend... (PRICE {bar.close}) (RSI {rsi10})')
		return False
	elif buy_triggered and bar.close < stop_loss and bar.close < sma5 and bar.close >= trade.planned_entry_price:
		logging.critical(f'{trade.ticker} moved above ENTRY {trade.planned_entry_price} and in an downward trend, but PRICE {bar.close} above ENTRY {trade.planned_entry_price}... (RSI {rsi10})')
		return False
	elif buy_triggered and bar.close < trade.stop_loss and bar.close < sma5 and bar.close < trade.planned_entry_price and rsi10 <= 65.0:
		logging.critical(f'{trade.ticker} moved above ENTRY {trade.planned_entry_price} and in an downward trend, but RSI below 65... (PRICE {bar.close}) (RSI {rsi10})')
		return False
	elif buy_triggered and bar.close < trade.stop_loss and bar.close < sma5 and bar.close < trade.planned_entry_price and rsi10 > 65.0:
		logging.critical(f'{trade.ticker} moved above ENTRY {trade.planned_entry_price} and in an downward trend with RSI {rsi10} above 65. Executing short sale at PRICE {bar.close}....')
		return True

	return False


def is_sellable(trade, bars, stock_math, trades_db):
	sma3 = stock_math.sma_3_close(bars)
	rsi10 = stock_math.rsi_10_close(bars)
	bar = bars[0]

	stop_loss = calculate_stop_loss(trade, trades_db, bar.close)

	logging.info(f'{trade.ticker}: OPEN PRICE {bar.close} SMA3 {sma3} RSI10 {rsi10} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {stop_loss}')

	now = datetime.utcnow()

	# Sell within last 30 minutes if marked for sale at end of the day
	if now.hour >= 19 and now.minute >= 30:
		if trade.sell_end_of_day == 1:
			logging.critical(f'{trade.ticker}: Trade is flagged for a sale at end of the day. Selling {trade.shares} shares at {now.hour}:{now.minute}...')
			return True

	# If the sma3 is less than or equal to the stop loss, we sell.
	if sma3 <= stop_loss:
		logging.critical(f'{trade.ticker}: STOP {stop_loss} exceeded by SMA3 {sma3}. Selling {trade.shares} shares...')
		return True

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
			return True
		else:
			logging.critical(f'{trade.ticker} exceeded the EXIT {trade.planned_exit_price}, but still in upward trend... (PRICE {bar.close}) (RSI {rsi10})')
			return False
	return False

def is_short_buyable(trade, bars, stock_math, trades_db):
	sma3 = stock_math.sma_3_close(bars)
	rsi10 = stock_math.rsi_10_close(bars)
	bar = bars[0]

	stop_loss = calculate_short_sale_stop_loss(trade, trades_db, bar.close)

	logging.info(f'{trade.ticker}: OPEN PRICE {bar.close} SMA3 {sma3} RSI10 {rsi10} ENTRY {trade.planned_entry_price} EXIT {trade.planned_exit_price} STOP {stop_loss}')

	now = datetime.utcnow()

	# Sell within last 30 minutes if marked for sale at end of the day
	if now.hour >= 19 and now.minute >= 30:
		if trade.sell_end_of_day == 1:
			logging.critical(f'{trade.ticker}: Trade is flagged for a sale at end of the day. Buying back {trade.shares} shares at {now.hour}:{now.minute}...')
			return True

	# If the sma3 is less than or equal to the stop loss, we sell.
	if sma3 >= stop_loss:
		logging.critical(f'{trade.ticker}: STOP {stop_loss} exceeded by SMA3 {sma3}. Buying back {trade.shares} shares...')
		return True

	#Once the price passes below within 1% of the exit price, we set a marker to buy, in case the price immediately moves into an upward trend
	if bar.close <= trade.planned_exit_price - (trade.planned_exit_price * 0.01):
		trades_db.set_sale_price_marker(trade.ticker, trade.id)

	sale_triggered = trades_db.get_sale_price_marker(trade.ticker, trade.id)

	# We only buy if the price is grater than the sma3 and therefore, in a upward trend OR has an RSI under 30, showing it's oversold. 
	if sale_triggered:
		if sma3 > bar.close or rsi10 < 30.0:
			if rsi10 < 30.0:
				logging.critical(f'{trade.ticker}: RSI {rsi10} is under 30. Stock is oversold. Buying back {trade.shares} shares at {bar.close}...')
			else:
				logging.critical(f'{trade.ticker}: PRICE {bar.close} less than SMA3 {sma3} with RSI {rsi10}. Trend has shifted. Buying back {trade.shares} shares...')
			return True
		else:
			logging.critical(f'{trade.ticker} dropped below the EXIT {trade.planned_exit_price}, but still in upward trend... (PRICE {bar.close}) (RSI {rsi10})')
			return False
	return False

def sell(brokerage, trades_db, trade, journal, price=None, amount=None):
	if price == None:
		shares = trade.shares
	else:
		if amount == None or amount == '' or amount == 0.0:
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
		else:
			trade_amount=amount

		# Shares are dynamically calculated from a percentage of the total brokerage account
		shares = math.trunc(trade_amount / price)

	order_id = brokerage.sell(trade.ticker, shares)
	if order_id is not None:
		if trade.type == 'short':
			trade = trades_db.sell_short(trade, order_id, shares)
		else:
			trade = trades_db.sell(trade, order_id)
		journal.update_trade_record(trade)
		logging.critical(f'{trade.ticker}: {trade.shares} shares sold or bought back at market price. (Order ID: {order_id})')
		return True
	else:
		logging.error('Brokerage API failed to complete sell order.')
		return False

def buy(brokerage, trades_db, bot_configuration, trade, journal, price=None, amount=None):

	if price == None:
		shares = trade.shares
	else:
		if amount == None or amount == '' or amount == 0.0:
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
		else:
			trade_amount=amount

		# Shares are dynamically calculated from a percentage of the total brokerage account
		shares = math.trunc(trade_amount / price)

	order_id = brokerage.buy(trade.ticker, shares)

	if order_id is not None:
		logging.critical(f'{trade.ticker}: {shares} shares bought or short sold at market price. (Order ID: {order_id})')
		if trade.type == 'short':
			trade = trades_db.buy_short(trade, order_id)
		else:
			trade = trades_db.buy(trade, shares, order_id)
		journal.update_trade_record(trade)
		return True
	else:
		logging.error('Brokerage API failed to complete buy order.')

	return False

def calculate_stop_loss(trade, trades_db, price):
	ath = trades_db.get_ath(trade.ticker, trade.id)
	if ath == None or price > ath:
		 trades_db.set_ath(trade.ticker, trade.id, price)
		 ath = trades_db.get_ath(trade.ticker, trade.id)

	if trade.stop_loss < 1.0:
		stop_loss = ath - (ath * trade.stop_loss)
	else:
		stop_loss = trade.stop_loss

	return stop_loss

def calculate_short_sale_stop_loss(trade, trades_db, price):
	ath = trades_db.get_ath(trade.ticker, trade.id)
	if ath == None or price > ath:
		 trades_db.set_ath(trade.ticker, trade.id, price)
		 ath = trades_db.get_ath(trade.ticker, trade.id)

	if trade.stop_loss < 1.0:
		stop_loss = ath + (ath * trade.stop_loss)
	else:
		stop_loss = trade.stop_loss

	return stop_loss
