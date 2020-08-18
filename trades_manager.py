import logging
import trades_db
import brokerage
import bot_configuration
import time

#def handle_open_buy_orders():

#def handle_open_sell_orders():

def handle_open_trades():
	raise Exception()
	logging.info('Handling open trades...')
	trades = trades_db.get_open_trades()

	for trade in trades:
		synced_trade = __sync_position__(trade)
		if synced_trade == None:
			__update_open_trade__(synced_trade)


def open_new_trades():
	logging.info('Opening new trades...')
	open_trades = trades_db.get_open_trades()

	if (len(open_trades) >= bot_configuration.MAX_TRADES_OPEN):
		return

	trades_to_open = bot_configuration.MAX_TRADES_OPEN - len(open_trades)
	queued_trades = trades_db.get_queued_trades()

	for trade in queued_trades:
		if queued_trades <= 0:
			break;

		if __update_queued_trade__(trade) == True:
			queued_trades -= 1

def __sync_position__(trade):
	position = brokerage.get_position(trade.ticker)

	if (position == None):
		logging.info(f'Missing position for {trade.create_date}. Marking as invalid...')
		trades_db.invalidate(trade.create_date)
		return None

	trades_db.sync(trade.create_date, position)
	return trades_db.get(trade.create_date)

def __update_open_trade__(trade):
	bar = brokerage.get_bar(trade.ticker)
	logging.debug(f'Trade: ticker: {trade.ticker}, planned_exit_price: {trade.planned_exit_price}, current_price: {bar.close}')

	if bar.close >= trade.planned_entry_price:
		if brokerage.buy(trade) == True:
			queued_trades -= 1
			trades_db.buy(trade.create_date)

	if bar.close <= trade.stop_loss:
		if brokerage.sell(trade) == True:
			trades_db.sell(trade.create_date)

	if bar.close >= trade.planned_exit_price:
		percentage_difference = (bar.close - trade.planned_exit_price) / trade.planned_exit_price
		if percentage_difference < bot_configuration.TRAILING_STOP_LOSS:
			trades_db.update_stop_loss(trade.create_date, bar.close)
		else:
			trades_db.update_stop_loss(trade.create_date, bar.close - (bar.close * bot_configuration.TRAILING_STOP_LOSS))

def __update_queued_trade__(trade):
	if trade.create_date + (60.0 * 60.0 * 24.0 * 7.0) >= time.time():
		trades_db.expire(trade.create_date)
	else:
		bar = brokerage.get_bar(trade.ticker)

		if bar.close >= trade.planned_entry_price:
			if brokerage.buy(trade) == True:
				trades_db.buy(trade.create_date)
				return True

	return False

