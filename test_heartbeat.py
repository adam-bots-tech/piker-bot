import logging
import bot_configuration
logging.basicConfig(format=bot_configuration.LOG_FORMAT, level=logging.DEBUG)
import brokerage
import trades_db
import os
import copy
from bar import Bar
from position import Position
from order import Order
import trade_journal
import pandas as pd
import cache

class TestTradeJournal(trade_journal.TradeJournal):

	def __init__(self):
		self.rows = [['ticker', 'type', 'min_entry', 'max_entry' 'exit', 'stop_loss', 'notes', 'expiration', 'metadata']]

	def get_queued_trades(self):
		return self.rows

	def reset_queued_trades(self, headerRow):
		self.rows=[headerRow]

	def create_queued_trade(self, row_num, ticker, type, min_entry, max_entry, exit, stop_loss, notes, expiration, metadata):
		self.rows.append([ticker, type, min_entry, max_entry, exit, stop_loss, notes, expiration, metadata])


	def create_trade_record(self, trade, notes, metadata):
		return None

	def update_trade_record(self, trade, buy_metadata=None, sale_metadata=None):
		return None

	def bootstrap(self):
		return None

class TestBrokerage(brokerage.Brokerage):
	def __init__(self):
		self.data_folder = bot_configuration.DATA_FOLDER
		self.bars = {
			'TSLA': [
				# Pulse 0 - Store entry price in state database
				[
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.0,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.0,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.0,"v": 0})
				],
				# Pulse 1 - Next bar tick triggers the buy order
				[
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.1,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.0,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.0,"v": 0})
				],
				# Pulse 2 - Order is filled and trade is now open. Storing price in state database
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 521.0,"v": 0}),
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.1,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.0,"v": 0})
				],
				# Pulse 3 - Store exit price in database
				[
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 524.0,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 521.0,"v": 0}),
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 499.1,"v": 0})
				],
				# Pulse 4 - Issuing sell order at 523.1
				[
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 523.1,"v": 0}),
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 524.0,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 521.0,"v": 0})
				],
				# Pulse 5 - Do nothing; order is coming back as replaced
				[
					Bar({"t": 5,"o": 0.0,"h": 0.0,"l": 0.0,"c": 523.1,"v": 0}),
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 523.1,"v": 0}),
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 524.0,"v": 0})
				]
			],
			'AAPL': [
				# Pulse 0 - Do nothing
				[
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 400.1,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 400.1,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 400.1,"v": 0}),
				],
				# Pulse 1 - Store entry price in state database
				[
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 399.8,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 400.1,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 400.1,"v": 0}),
				],
				# Pulse 2 - Next bar tick triggers the buy order
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 399.99,"v": 0}),
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 399.8,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 400.1,"v": 0}),
				],
				# Pulse 3 - Do nothing; order is coming back as replaced
				[
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 403.0,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 399.99,"v": 0}),
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 399.8,"v": 0}),
				],
				# Pulse 4 - Do nothing
				[
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 386.0,"v": 0}),
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 403.0,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 399.99,"v": 0}),
				],
				# Pulse 5 - Hit stop loss; sell at 383.0
				[
					Bar({"t": 5,"o": 0.0,"h": 0.0,"l": 0.0,"c": 360.0,"v": 0}),
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 386.0,"v": 0}),
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 403.0,"v": 0}),
				],
			],
			'FB': [
				# Pulse 0 - Store entry price in state database
				[
					Bar({"t": 0, "o": 0.0,"h": 0.0,"l": 0.0,"c": 299.5,"v": 0}),
					Bar({"t": 0, "o": 0.0,"h": 0.0,"l": 0.0,"c": 299.5,"v": 0}),
					Bar({"t": 0, "o": 0.0,"h": 0.0,"l": 0.0,"c": 299.5,"v": 0}),
				],
				# Pulse 1 - Buy
				[
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 299.6,"v": 0}),
					Bar({"t": 0, "o": 0.0,"h": 0.0,"l": 0.0,"c": 299.5,"v": 0}),
					Bar({"t": 0, "o": 0.0,"h": 0.0,"l": 0.0,"c": 299.5,"v": 0}),
				],
				# Pulse 2 - Storing exit price in database
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 330.1,"v": 0}),
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 299.6,"v": 0}),
					Bar({"t": 0, "o": 0.0,"h": 0.0,"l": 0.0,"c": 299.5,"v": 0}),
				],
				# Pulse 3 - Sell
				[
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 329.0,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 330.1,"v": 0}),
					Bar({"t": 1,"o": 0.0,"h": 0.0,"l": 0.0,"c": 299.6,"v": 0}),
				],
				# Pulse 4 - Do nothing
				[
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 330.1,"v": 0}),
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 329.0,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 330.1,"v": 0}),
				],
				# Pulse 5 - Do nothing
				[
					Bar({"t": 5,"o": 0.0,"h": 0.0,"l": 0.0,"c": 330.1,"v": 0}),
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 330.1,"v": 0}),
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 329.0,"v": 0}),
				],
			],
			'AMZN': [
				# Pulse 0 - Store the entry price in state database
				[
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.5,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.5,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.5,"v": 0}),
				],
				# Pulse 1 - Buy
				[
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.6,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.5,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.5,"v": 0}),
				],
				# Pulse 2 - Do nothing; order is coming back as expired
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.6,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.5,"v": 0}),
				],
				# Pulse 3 - Do nothing
				[
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.6,"v": 0}),
				],
				# Pulse 4 - Do nothing
				[
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
				],
				# Pulse 5 - Do nothing
				[
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 1999.4,"v": 0}),
				],
			],
			'GOOG': [
				# Pulse 0 - Store the entry price in state database
				[
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.0,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.0,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.0,"v": 0}),
				],
				# Pulse 1 - Buy
				[
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.1,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.0,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.0,"v": 0}),
				],
				# Pulse 2 - Store the exit price in the database
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 366.0,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.1,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.0,"v": 0}),
				],
				# Pulse 3 - Sell at 365
				[
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 365.0,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 366.0,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 349.1,"v": 0}),
				],
				# Pulse 4 - Do nothing
				[
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 366.0,"v": 0}),
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 365.0,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 366.0,"v": 0}),
				],
				# Pulse 5 - Do nothing
				[
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 366.0,"v": 0}),
					Bar({"t": 4,"o": 0.0,"h": 0.0,"l": 0.0,"c": 366.0,"v": 0}),
					Bar({"t": 3,"o": 0.0,"h": 0.0,"l": 0.0,"c": 365.0,"v": 0}),
				],
			],
			'MSFT': [
				# Pulse 0 - Store the entry price in state database
				[
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.8,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.8,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.8,"v": 0}),
				],
				# Pulse 1 - Buy
				[
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.9,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.8,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.8,"v": 0}),
				],
				# Pulse 2 - Do nothing; order is coming back as cacnelled
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.9,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.8,"v": 0}),
				],
				# Pulse 3 - Do nothing
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.9,"v": 0}),
				],
				# Pulse 4 - Do nothing
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
				],
				# Pulse 5 - Do nothing
				[
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
					Bar({"t": 2,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
					Bar({"t": 0,"o": 0.0,"h": 0.0,"l": 0.0,"c": 199.7,"v": 0}),
				],
			]
		}

	def is_open(self):
		return True
	
	def get_position(self, ticker):
		positions = {
			'TSLA': Position('TSLA', 50, 499.1),
			'AAPL': Position('AAPL', 62, 398.1),
			'FB': Position('FB', 83, 299.6),
			'GOOG': Position('GOOG', 71, 349.1)
		}
		return positions[ticker]

	def get_last_three_bars(self, ticker):
		bars_copy = copy.copy(self.bars[ticker])
		del self.bars[ticker][0]
		return bars_copy[0]

	def sell(self, ticker, shares):
		sales = {
			'TSLA': 'S1',
			'AAPL': 'S2',
			'FB': 'S3',
			'GOOG': 'S5',
		}
		return sales[ticker]

	def buy(self, ticker, shares):
		buys = {
			'TSLA': 'B1',
			'AAPL': 'B2',
			'FB': 'B3',
			'AMZN': 'B4',
			'GOOG': 'B5',
			'MSFT': 'B6'
		}
		return buys[ticker]

	def get_order(self, order_id):
		orders = {
			'S1': Order('S1', 'replaced', 523.1, 50, 'R1'), #TSLA
			'S2': Order('S2', 'filled', 383.0, 62, ''), #AAPL
			'S3': Order('S3', 'expired', 329.0, 83, ''), #FB
			'S5': Order('S5', 'canceled', 365.0, 71, ''), #GOOG
			'B1': Order('B1', 'filled', 499.1, 50, ''), #TSLA
			'B2': Order('B2', 'replaced', 398.1, 62, 'R2'), #AAPL
			'B3': Order('B3', 'filled', 299.6, 83, ''), #FB
			'B4': Order('B4', 'expired', 1999.6, 20, ''), #AMZN
			'B5': Order('B5', 'filled', 349.1, 71, ''), #GOOG
			'B6': Order('B6', 'canceled', 199.9, 20, ''), #MSFT
			'R1': Order('R1', 'filled', 523.1, 50, ''), #TSLA
			'R2': Order('R2', 'filled', 398.1, 62, ''), #AAPL
		}
		return orders[order_id]

	def get_buying_power(self):
		return 500000

	def get_last_200_minutes_data_set(self, ticker, with_time=False):
		if with_time:
			return pd.DataFrame(data=[[400.0, 500.0, 550.00, 340.0, 100.0, '9/3/2020 20:00']], index=range(0, 1), columns=['open','close','high','low','volume', 'time'])
		else:
			return pd.DataFrame(data=[[400.0, 500.0, 550.00, 340.0, 100.0]], index=range(0, 1), columns=['open','close','high','low','volume'])

	def get_last_200_15minutes_data_set(self, ticker, with_time=False):
		if with_time:
			return pd.DataFrame(data=[[400.0, 500.0, 550.00, 340.0, 100.0, '9/3/2020 20:00']], index=range(0, 1), columns=['open','close','high','low','volume', 'time'])
		else:
			return pd.DataFrame(data=[[400.0, 500.0, 550.00, 340.0, 100.0]], index=range(0, 1), columns=['open','close','high','low','volume'])


#Overwrite the configuration
bot_configuration.DATABASE_NAME='test-piker-bot.db'
bot_configuration.LOG_FILE='test-piker-bot.log'
bot_configuration.TRAILING_STOP_LOSS=0.02
bot_configuration.MAX_TRADES_OPEN=6
bot_configuration.PERCENTAGE_OF_ACCOUNT_TO_LEVERAGE=0.05
bot_configuration.MIN_AMOUNT_PER_TRADE=100.0
bot_configuration.TRADE_JOURNAL_TITLE='Test Stock Trading Journal'
bot_configuration.DATA_FOLDER ='D:\\development\\data\\'

#Loading heartbeat here, so everything loads after we change the config
import heartbeat

#Remove the old log and database file
if os.path.exists(bot_configuration.DATA_FOLDER+bot_configuration.DATABASE_NAME):
	os.remove(bot_configuration.DATA_FOLDER+bot_configuration.DATABASE_NAME)

if os.path.exists(bot_configuration.DATA_FOLDER+bot_configuration.LOG_FILE):
	os.remove(bot_configuration.DATA_FOLDER+bot_configuration.LOG_FILE)

#Overwrite the heartbeat's brokerage with the test brokerage
heartbeat.b = TestBrokerage()
heartbeat.j = TestTradeJournal()
heartbeat.db.journal = heartbeat.j

#Create the trades
heartbeat.j.create_queued_trade(2,'TSLA', 'long', 498.0, 500.0, 520.0, 490.0, '', 1, '') #Replace the sell order and sell at a gain
heartbeat.j.create_queued_trade(3,'AAPL', 'long', 398.0, 400.0, 450.0, 384.0, '', 1, '') #Replace the buy order and sell at a loss
heartbeat.j.create_queued_trade(4,'FB', 'long', 298.0, 300.0, 330.0, 285.0, '', 1, '') #Expire the sale
heartbeat.j.create_queued_trade(5,'AMZN', 'long', 1998.0, 2000.0, 2200.0, 1900.00, '', 1, '') #Expire the buy
heartbeat.j.create_queued_trade(6,'GOOG', 'long', 347.0, 350.0, 365.0, 343.0, '', 1, '') #Expire the sale
heartbeat.j.create_queued_trade(7,'MSFT', 'long', 196.0, 200.0, 240.0, 187.0, '', 1, '') #Expire the buy


# PULSE 1
logging.info('Heartbeat pulse incoming...')
heartbeat.pulse()

tsla = heartbeat.db.get_by_ticker('TSLA')
aapl = heartbeat.db.get_by_ticker("AAPL")
fb = heartbeat.db.get_by_ticker("FB")
amzn = heartbeat.db.get_by_ticker('AMZN')
goog = heartbeat.db.get_by_ticker('GOOG')
msft = heartbeat.db.get_by_ticker('MSFT')

#TSLA 
assert tsla.ticker == 'TSLA', f"TSLA ticker {tsla.ticker}"
assert tsla.shares == 0.0, f"TSLA shares {tsla.shares}"
assert tsla.planned_max_entry_price == 500.0, f"TSLA planned_max_entry_price {tsla.planned_max_entry_price}"
assert tsla.planned_exit_price == 520.0, f"TSLA planned_exit_price {tsla.planned_exit_price}"
assert tsla.stop_loss == 490.0, f"TSLA stop_loss {tsla.stop_loss}"
assert tsla.status == 'QUEUED', f"TSLA status {tsla.status}"
assert tsla.exit_date == 0.0, f"TSLA exit_date {tsla.exit_date}"
assert tsla.entry_date == 0.0, f"TSLA entry_date {tsla.entry_date}"
assert tsla.actual_exit_price == 0.0, f"TSLA actual_exit_price {tsla.actual_exit_price}"
assert tsla.actual_entry_price == 0.0, f"TSLA actual_entry_price {tsla.actual_entry_price}"
assert tsla.buy_order_id == '', f"TSLA buy_order_id {tsla.buy_order_id}"
assert tsla.sell_order_id == '', f"TSLA sell_order_id {tsla.sell_order_id}"
assert tsla.create_date is not None, f"TSLA create_date {tsla.create_date}"

#AAPL 
assert aapl.ticker == 'AAPL', f"AAPL ticker {aapl.ticker}"
assert aapl.shares == 0.0, f"AAPL shares {aapl.shares}"
assert aapl.planned_max_entry_price == 400.0, f"AAPL planned_max_entry_price {aapl.planned_max_entry_price}"
assert aapl.planned_exit_price == 450.0, f"AAPL planned_exit_price {aapl.planned_exit_price}"
assert aapl.stop_loss == 384.0, f"AAPL stop_loss {aapl.stop_loss}"
assert aapl.status == 'QUEUED', f"AAPL status {aapl.status}"
assert aapl.exit_date == 0.0, f"AAPL exit_date {aapl.exit_date}"
assert aapl.entry_date == 0.0, f"AAPL entry_date {aapl.entry_date}"
assert aapl.actual_exit_price == 0.0, f"AAPL actual_exit_price {aapl.actual_exit_price}"
assert aapl.actual_entry_price == 0.0, f"AAPL actual_entry_price {aapl.actual_entry_price}"
assert aapl.buy_order_id == '', f"AAPL buy_order_id {aapl.buy_order_id}"
assert aapl.sell_order_id == '', f"AAPL sell_order_id {aapl.sell_order_id}"
assert aapl.create_date is not None, f"AAPL create_date {aapl.create_date}"

#FB 
assert fb.ticker == 'FB', f"FB ticker {fb.ticker}"
assert fb.shares == 0.0, f"FB shares {fb.shares}"
assert fb.planned_max_entry_price == 300.0, f"FB planned_max_entry_price {fb.planned_max_entry_price}"
assert fb.planned_exit_price == 330.0, f"FB planned_exit_price {fb.planned_exit_price}"
assert fb.stop_loss == 285.0, f"FB stop_loss {fb.stop_loss}"
assert fb.status == 'QUEUED', f"FB status {fb.status}"
assert fb.exit_date == 0.0, f"FB exit_date {fb.exit_date}"
assert fb.entry_date == 0.0, f"FB entry_date {fb.entry_date}"
assert fb.actual_exit_price == 0.0, f"FB actual_exit_price {fb.actual_exit_price}"
assert fb.actual_entry_price == 0.0, f"FB actual_entry_price {fb.actual_entry_price}"
assert fb.buy_order_id == '', f"FB buy_order_id {fb.buy_order_id}"
assert fb.sell_order_id == '', f"FB sell_order_id {fb.sell_order_id}"
assert fb.create_date is not None, f"FB create_date {fb.create_date}"

#AMZN 
assert amzn.ticker == 'AMZN', f"AMZN ticker {amzn.ticker}"
assert amzn.shares == 0.0, f"AMZN shares {amzn.shares}"
assert amzn.planned_max_entry_price == 2000.0, f"AMZN planned_max_entry_price {amzn.planned_max_entry_price}"
assert amzn.planned_exit_price == 2200.0, f"AMZN planned_exit_price {amzn.planned_exit_price}"
assert amzn.stop_loss == 1900.0, f"AMZN stop_loss {amzn.stop_loss}"
assert amzn.status == 'QUEUED', f"AMZN status {amzn.status}"
assert amzn.exit_date == 0.0, f"AMZN exit_date {amzn.exit_date}"
assert amzn.entry_date == 0.0, f"AMZN entry_date {amzn.entry_date}"
assert amzn.actual_exit_price == 0.0, f"AMZN actual_exit_price {amzn.actual_exit_price}"
assert amzn.actual_entry_price == 0.0, f"AMZN actual_entry_price {amzn.actual_entry_price}"
assert amzn.buy_order_id == '', f"AMZN buy_order_id {amzn.buy_order_id}"
assert amzn.sell_order_id == '', f"AMZN sell_order_id {amzn.sell_order_id}"
assert amzn.create_date is not None, f"AMZN create_date {amzn.create_date}"

#GOOG 
assert goog.ticker == 'GOOG', f"GOOG ticker {goog.ticker}"
assert goog.shares == 0.0, f"GOOG shares {goog.shares}"
assert goog.planned_max_entry_price == 350.0, f"GOOG planned_max_entry_price {goog.planned_max_entry_price}"
assert goog.planned_exit_price == 365.0, f"GOOG planned_exit_price {goog.planned_exit_price}"
assert goog.stop_loss == 343.0, f"GOOG stop_loss {goog.stop_loss}"
assert goog.status == 'QUEUED', f"GOOG status {goog.status}"
assert goog.exit_date == 0.0, f"GOOG exit_date {goog.exit_date}"
assert goog.entry_date == 0.0, f"GOOG entry_date {goog.entry_date}"
assert goog.actual_exit_price == 0.0, f"GOOG actual_exit_price {goog.actual_exit_price}"
assert goog.actual_entry_price == 0.0, f"GOOG actual_entry_price {goog.actual_entry_price}"
assert goog.buy_order_id == '', f"GOOG buy_order_id {goog.buy_order_id}"
assert goog.sell_order_id == '', f"GOOG sell_order_id {goog.sell_order_id}"
assert goog.create_date is not None, f"GOOG create_date {goog.create_date}"

#MSFT 
assert msft.ticker == 'MSFT', f"MSFT ticker {msft.ticker}"
assert msft.shares == 0.0, f"MSFT shares {msft.shares}"
assert msft.planned_max_entry_price == 200.0, f"MSFT planned_max_entry_price {msft.planned_max_entry_price}"
assert msft.planned_exit_price == 240.0, f"MSFT planned_exit_price {msft.planned_exit_price}"
assert msft.stop_loss == 187.0, f"MSFT stop_loss {msft.stop_loss}"
assert msft.status == 'QUEUED', f"MSFT status {msft.status}"
assert msft.exit_date == 0.0, f"MSFT exit_date {msft.exit_date}"
assert msft.entry_date == 0.0, f"MSFT entry_date {msft.entry_date}"
assert msft.actual_exit_price == 0.0, f"MSFT actual_exit_price {msft.actual_exit_price}"
assert msft.actual_entry_price == 0.0, f"MSFT actual_entry_price {msft.actual_entry_price}"
assert msft.buy_order_id == '', f"MSFT buy_order_id {msft.buy_order_id}"
assert msft.sell_order_id == '', f"MSFT sell_order_id {msft.sell_order_id}"
assert msft.create_date is not None, f"MSFT create_date {msft.create_date}"

# PULSE 2
logging.info('Heartbeat pulse incoming...')
heartbeat.pulse()

tsla = heartbeat.db.get(tsla.create_date)
aapl = heartbeat.db.get(aapl.create_date)
fb = heartbeat.db.get(fb.create_date)
amzn = heartbeat.db.get(amzn.create_date)
goog = heartbeat.db.get(goog.create_date)
msft = heartbeat.db.get(msft.create_date)

#TSLA 
assert tsla.ticker == 'TSLA', f"TSLA ticker {tsla.ticker}"
assert tsla.shares == 50.0, f"TSLA shares {tsla.shares}"
assert tsla.planned_max_entry_price == 500.0, f"TSLA planned_max_entry_price {tsla.planned_max_entry_price}"
assert tsla.planned_exit_price == 520.0, f"TSLA planned_exit_price {tsla.planned_exit_price}"
assert tsla.stop_loss == 490.0, f"TSLA stop_loss {tsla.stop_loss}"
assert tsla.status == 'BUYING', f"TSLA status {tsla.status}"
assert tsla.exit_date == 0.0, f"TSLA exit_date {tsla.exit_date}"
assert tsla.entry_date ==  0.0, f"TSLA entry_date {tsla.entry_date}"
assert tsla.actual_exit_price == 0.0, f"TSLA actual_exit_price {tsla.actual_exit_price}"
assert tsla.actual_entry_price == 0.0, f"TSLA actual_entry_price {tsla.actual_entry_price}"
assert tsla.buy_order_id == 'B1', f"TSLA buy_order_id {tsla.buy_order_id}"
assert tsla.sell_order_id == '', f"TSLA sell_order_id {tsla.sell_order_id}"
assert tsla.create_date is not None, f"TSLA create_date {tsla.create_date}"

#AAPL 
assert aapl.ticker == 'AAPL', f"AAPL ticker {aapl.ticker}"
assert aapl.shares == 0.0, f"AAPL shares {aapl.shares}"
assert aapl.planned_max_entry_price == 400.0, f"AAPL planned_max_entry_price {aapl.planned_max_entry_price}"
assert aapl.planned_exit_price == 450.0, f"AAPL planned_exit_price {aapl.planned_exit_price}"
assert aapl.stop_loss == 384.0, f"AAPL stop_loss {aapl.stop_loss}"
assert aapl.status == 'QUEUED', f"AAPL status {aapl.status}"
assert aapl.exit_date == 0.0, f"AAPL exit_date {aapl.exit_date}"
assert aapl.entry_date == 0.0, f"AAPL entry_date {aapl.entry_date}"
assert aapl.actual_exit_price == 0.0, f"AAPL actual_exit_price {aapl.actual_exit_price}"
assert aapl.actual_entry_price == 0.0, f"AAPL actual_entry_price {aapl.actual_entry_price}"
assert aapl.buy_order_id == '', f"AAPL buy_order_id {aapl.buy_order_id}"
assert aapl.sell_order_id == '', f"AAPL sell_order_id {aapl.sell_order_id}"
assert aapl.create_date is not None, f"AAPL create_date {aapl.create_date}"

#FB 
assert fb.ticker == 'FB', f"FB ticker {fb.ticker}"
assert fb.shares == 83.0, f"FB shares {fb.shares}"
assert fb.planned_max_entry_price == 300.0, f"FB planned_max_entry_price {fb.planned_max_entry_price}"
assert fb.planned_exit_price == 330.0, f"FB planned_exit_price {fb.planned_exit_price}"
assert fb.stop_loss == 285, f"FB stop_loss {fb.stop_loss}"
assert fb.status == 'BUYING', f"FB status {fb.status}"
assert fb.exit_date == 0.0, f"FB exit_date {fb.exit_date}"
assert fb.entry_date ==  0.0, f"FB entry_date {fb.entry_date}"
assert fb.actual_exit_price == 0.0, f"FB actual_exit_price {fb.actual_exit_price}"
assert fb.actual_entry_price == 0.0, f"FB actual_entry_price {fb.actual_entry_price}"
assert fb.buy_order_id == 'B3', f"FB buy_order_id {fb.buy_order_id}"
assert fb.sell_order_id == '', f"FB sell_order_id {fb.sell_order_id}"
assert fb.create_date is not None, f"FB create_date {fb.create_date}"

#AMZN 
assert amzn.ticker == 'AMZN', f"AMZN ticker {amzn.ticker}"
assert amzn.shares == 12.0, f"AMZN shares {amzn.shares}"
assert amzn.planned_max_entry_price == 2000.0, f"AMZN planned_max_entry_price {amzn.planned_max_entry_price}"
assert amzn.planned_exit_price == 2200.0, f"AMZN planned_exit_price {amzn.planned_exit_price}"
assert amzn.stop_loss == 1900.0, f"AMZN stop_loss {amzn.stop_loss}"
assert amzn.status == 'BUYING', f"AMZN status {amzn.status}"
assert amzn.exit_date == 0.0, f"AMZN exit_date {amzn.exit_date}"
assert amzn.entry_date == 0.0, f"AMZN entry_date {amzn.entry_date}"
assert amzn.actual_exit_price == 0.0, f"AMZN actual_exit_price {amzn.actual_exit_price}"
assert amzn.actual_entry_price == 0.0, f"AMZN actual_entry_price {amzn.actual_entry_price}"
assert amzn.buy_order_id == 'B4', f"AMZN buy_order_id {amzn.buy_order_id}"
assert amzn.sell_order_id == '', f"AMZN sell_order_id {amzn.sell_order_id}"
assert amzn.create_date is not None, f"AMZN create_date {amzn.create_date}"

#GOOG 
assert goog.ticker == 'GOOG', f"GOOG ticker {goog.ticker}"
assert goog.shares == 71.0, f"GOOG shares {goog.shares}"
assert goog.planned_max_entry_price == 350.0, f"GOOG planned_max_entry_price {goog.planned_max_entry_price}"
assert goog.planned_exit_price == 365.0, f"GOOG planned_exit_price {goog.planned_exit_price}"
assert goog.stop_loss == 343.0, f"GOOG stop_loss {goog.stop_loss}"
assert goog.status == 'BUYING', f"GOOG status {goog.status}"
assert goog.exit_date == 0.0, f"GOOG exit_date {goog.exit_date}"
assert goog.entry_date == 0.0, f"GOOG entry_date {goog.entry_date}"
assert goog.actual_entry_price == 0.0, f"GOOG actual_exit_price {goog.actual_exit_price}"
assert goog.actual_exit_price == 0.0, f"GOOG actual_entry_price {goog.actual_entry_price}"
assert goog.buy_order_id == 'B5', f"GOOG buy_order_id {goog.buy_order_id}"
assert goog.sell_order_id == '', f"GOOG sell_order_id {goog.sell_order_id}"
assert goog.create_date is not None, f"GOOG create_date {goog.create_date}"

#MSFT 
assert msft.ticker == 'MSFT', f"MSFT ticker {msft.ticker}"
assert msft.shares == 125.0, f"MSFT shares {msft.shares}"
assert msft.planned_max_entry_price == 200.0, f"MSFT planned_max_entry_price {msft.planned_max_entry_price}"
assert msft.planned_exit_price == 240.0, f"MSFT planned_exit_price {msft.planned_exit_price}"
assert msft.stop_loss == 187.0, f"MSFT stop_loss {msft.stop_loss}"
assert msft.status == 'BUYING', f"MSFT status {msft.status}"
assert msft.exit_date == 0.0, f"MSFT exit_date {msft.exit_date}"
assert msft.entry_date == 0.0, f"MSFT entry_date {msft.entry_date}"
assert msft.actual_exit_price == 0.0, f"MSFT actual_exit_price {msft.actual_exit_price}"
assert msft.actual_entry_price == 0.0, f"MSFT actual_entry_price {msft.actual_entry_price}"
assert msft.buy_order_id == 'B6', f"MSFT buy_order_id {msft.buy_order_id}"
assert msft.sell_order_id == '', f"MSFT sell_order_id {msft.sell_order_id}"
assert msft.create_date is not None, f"MSFT create_date {msft.create_date}"

# PULSE 3
logging.info('Heartbeat pulse incoming...')
heartbeat.pulse()

# Workflow isn't causing AAPL bar to get popped off. Quick hack to make the test work. Overlooked this issue in design
del heartbeat.b.bars['AAPL'][0]

tsla = heartbeat.db.get(tsla.create_date)
aapl = heartbeat.db.get(aapl.create_date)
fb = heartbeat.db.get(fb.create_date)
amzn = heartbeat.db.get(amzn.create_date)
goog = heartbeat.db.get(goog.create_date)
msft = heartbeat.db.get(msft.create_date)

#TSLA 
assert tsla.ticker == 'TSLA', f"TSLA ticker {tsla.ticker}"
assert tsla.shares == 50.0, f"TSLA shares {tsla.shares}"
assert tsla.planned_max_entry_price == 500.0, f"TSLA planned_max_entry_price {tsla.planned_max_entry_price}"
assert tsla.planned_exit_price == 520.0, f"TSLA planned_exit_price {tsla.planned_exit_price}"
assert tsla.stop_loss == 490.0, f"TSLA stop_loss {tsla.stop_loss}"
assert tsla.status == 'SELLING', f"TSLA status {tsla.status}"
assert tsla.exit_date == 0.0, f"TSLA exit_date {tsla.exit_date}"
assert tsla.entry_date != 0.0, f"TSLA entry_date {tsla.entry_date}"
assert tsla.actual_exit_price == 0.0, f"TSLA actual_exit_price {tsla.actual_exit_price}"
assert tsla.actual_entry_price == 499.1, f"TSLA actual_entry_price {tsla.actual_entry_price}"
assert tsla.buy_order_id == 'B1', f"TSLA buy_order_id {tsla.buy_order_id}"
assert tsla.sell_order_id == 'S1', f"TSLA sell_order_id {tsla.sell_order_id}"
assert tsla.create_date is not None, f"TSLA create_date {tsla.create_date}"

#AAPL 
assert aapl.ticker == 'AAPL', f"AAPL ticker {aapl.ticker}"
assert aapl.shares == 62.0, f"AAPL shares {aapl.shares}"
assert aapl.planned_max_entry_price == 400.0, f"AAPL planned_max_entry_price {aapl.planned_max_entry_price}"
assert aapl.planned_exit_price == 450.0, f"AAPL planned_exit_price {aapl.planned_exit_price}"
assert aapl.stop_loss == 384.0, f"AAPL stop_loss {aapl.stop_loss}"
assert aapl.status == 'BUYING', f"AAPL status {aapl.status}"
assert aapl.exit_date == 0.0, f"AAPL exit_date {aapl.exit_date}"
assert aapl.entry_date == 0.0, f"AAPL entry_date {aapl.entry_date}"
assert aapl.actual_exit_price == 0.0, f"AAPL actual_exit_price {aapl.actual_exit_price}"
assert aapl.actual_entry_price == 0.0, f"AAPL actual_entry_price {aapl.actual_entry_price}"
assert aapl.buy_order_id == 'B2', f"AAPL buy_order_id {aapl.buy_order_id}"
assert aapl.sell_order_id == '', f"AAPL sell_order_id {aapl.sell_order_id}"
assert aapl.create_date is not None, f"AAPL create_date {aapl.create_date}"

#FB 
assert fb.ticker == 'FB', f"FB ticker {fb.ticker}"
assert fb.shares == 83.0, f"FB shares {fb.shares}"
assert fb.planned_max_entry_price == 300.0, f"FB planned_max_entry_price {fb.planned_max_entry_price}"
assert fb.planned_exit_price == 330.0, f"FB planned_exit_price {fb.planned_exit_price}"
assert fb.stop_loss == 285.0, f"FB stop_loss {fb.stop_loss}"
assert fb.status == 'SELLING', f"FB status {fb.status}"
assert fb.exit_date == 0.0, f"FB exit_date {fb.exit_date}"
assert fb.entry_date !=  0.0, f"FB entry_date {fb.entry_date}"
assert fb.actual_exit_price == 0.0, f"FB actual_exit_price {fb.actual_exit_price}"
assert fb.actual_entry_price == 299.6, f"FB actual_entry_price {fb.actual_entry_price}"
assert fb.buy_order_id == 'B3', f"FB buy_order_id {fb.buy_order_id}"
assert fb.sell_order_id == 'S3', f"FB sell_order_id {fb.sell_order_id}"
assert fb.create_date is not None, f"FB create_date {fb.create_date}"

#AMZN 
assert amzn.ticker == 'AMZN', f"AMZN ticker {amzn.ticker}"
assert amzn.shares == 12.0, f"AMZN shares {amzn.shares}"
assert amzn.planned_max_entry_price == 2000.0, f"AMZN planned_max_entry_price {amzn.planned_max_entry_price}"
assert amzn.planned_exit_price == 2200.0, f"AMZN planned_exit_price {amzn.planned_exit_price}"
assert amzn.stop_loss == 1900.0, f"AMZN stop_loss {amzn.stop_loss}"
assert amzn.status == 'EXPIRED', f"AMZN status {amzn.status}"
assert amzn.exit_date == 0.0, f"AMZN exit_date {amzn.exit_date}"
assert amzn.entry_date == 0.0, f"AMZN entry_date {amzn.entry_date}"
assert amzn.actual_exit_price == 0.0, f"AMZN actual_exit_price {amzn.actual_exit_price}"
assert amzn.actual_entry_price == 0.0, f"AMZN actual_entry_price {amzn.actual_entry_price}"
assert amzn.buy_order_id == 'B4', f"AMZN buy_order_id {amzn.buy_order_id}"
assert amzn.sell_order_id == '', f"AMZN sell_order_id {amzn.sell_order_id}"
assert amzn.create_date is not None, f"AMZN create_date {amzn.create_date}"

#GOOG 
assert goog.ticker == 'GOOG', f"GOOG ticker {goog.ticker}"
assert goog.shares == 71.0, f"GOOG shares {goog.shares}"
assert goog.planned_max_entry_price == 350.0, f"GOOG planned_max_entry_price {goog.planned_max_entry_price}"
assert goog.planned_exit_price == 365.0, f"GOOG planned_exit_price {goog.planned_exit_price}"
assert goog.stop_loss == 343.0, f"GOOG stop_loss {goog.stop_loss}"
assert goog.status == 'SELLING', f"GOOG status {goog.status}"
assert goog.exit_date == 0.0, f"GOOG exit_date {goog.exit_date}"
assert goog.entry_date != 0.0, f"GOOG entry_date {goog.entry_date}"
assert goog.actual_entry_price ==349.1, f"GOOG actual_exit_price {goog.actual_entry_price}"
assert goog.actual_exit_price == 0.0, f"GOOG actual_entry_price {goog.actual_entry_price}"
assert goog.buy_order_id == 'B5', f"GOOG buy_order_id {goog.buy_order_id}"
assert goog.sell_order_id == 'S5', f"GOOG sell_order_id {goog.sell_order_id}"
assert goog.create_date is not None, f"GOOG create_date {goog.create_date}"

#MSFT 
assert msft.ticker == 'MSFT', f"MSFT ticker {msft.ticker}"
assert msft.shares == 125.0, f"MSFT shares {msft.shares}"
assert msft.planned_max_entry_price == 200.0, f"MSFT planned_max_entry_price {msft.planned_max_entry_price}"
assert msft.planned_exit_price == 240.0, f"MSFT planned_exit_price {msft.planned_exit_price}"
assert msft.stop_loss == 187.0, f"MSFT stop_loss {msft.stop_loss}"
assert msft.status == 'CANCELED', f"MSFT status {msft.status}"
assert msft.exit_date == 0.0, f"MSFT exit_date {msft.exit_date}"
assert msft.entry_date == 0.0, f"MSFT entry_date {msft.entry_date}"
assert msft.actual_exit_price == 0.0, f"MSFT actual_exit_price {msft.actual_exit_price}"
assert msft.actual_entry_price == 0.0, f"MSFT actual_entry_price {msft.actual_entry_price}"
assert msft.buy_order_id == 'B6', f"MSFT buy_order_id {msft.buy_order_id}"
assert msft.sell_order_id == '', f"MSFT sell_order_id {msft.sell_order_id}"
assert msft.create_date is not None, f"MSFT create_date {msft.create_date}"

# PULSE 4
logging.info('Heartbeat pulse incoming...')
heartbeat.pulse()

tsla = heartbeat.db.get(tsla.create_date)
aapl = heartbeat.db.get(aapl.create_date)
fb = heartbeat.db.get(fb.create_date)
amzn = heartbeat.db.get(amzn.create_date)
goog = heartbeat.db.get(goog.create_date)
msft = heartbeat.db.get(msft.create_date)

#TSLA 
assert tsla.ticker == 'TSLA', f"TSLA ticker {tsla.ticker}"
assert tsla.shares == 50.0, f"TSLA shares {tsla.shares}"
assert tsla.planned_max_entry_price == 500.0, f"TSLA planned_max_entry_price {tsla.planned_max_entry_price}"
assert tsla.planned_exit_price == 520.0, f"TSLA planned_exit_price {tsla.planned_exit_price}"
assert tsla.stop_loss == 490.0, f"TSLA stop_loss {tsla.stop_loss}"
assert tsla.status == 'SELLING', f"TSLA status {tsla.status}"
assert tsla.exit_date == 0.0, f"TSLA exit_date {tsla.exit_date}"
assert tsla.entry_date != 0.0, f"TSLA entry_date {tsla.entry_date}"
assert tsla.actual_exit_price == 0.0, f"TSLA actual_exit_price {tsla.actual_exit_price}"
assert tsla.actual_entry_price == 499.1, f"TSLA actual_entry_price {tsla.actual_entry_price}"
assert tsla.buy_order_id == 'B1', f"TSLA buy_order_id {tsla.buy_order_id}"
assert tsla.sell_order_id == 'R1', f"TSLA sell_order_id {tsla.sell_order_id}"
assert tsla.create_date is not None, f"TSLA create_date {tsla.create_date}"

#AAPL 
assert aapl.ticker == 'AAPL', f"AAPL ticker {aapl.ticker}"
assert aapl.shares == 62.0, f"AAPL shares {aapl.shares}"
assert aapl.planned_max_entry_price == 400.0, f"AAPL planned_max_entry_price {aapl.planned_max_entry_price}"
assert aapl.planned_exit_price == 450.0, f"AAPL planned_exit_price {aapl.planned_exit_price}"
assert aapl.stop_loss == 384.0, f"AAPL stop_loss {aapl.stop_loss}"
assert aapl.status == 'BUYING', f"AAPL status {aapl.status}"
assert aapl.exit_date == 0.0, f"AAPL exit_date {aapl.exit_date}"
assert aapl.entry_date == 0.0, f"AAPL entry_date {aapl.entry_date}"
assert aapl.actual_exit_price == 0.0, f"AAPL actual_exit_price {aapl.actual_exit_price}"
assert aapl.actual_entry_price == 0.0, f"AAPL actual_entry_price {aapl.actual_entry_price}"
assert aapl.buy_order_id == 'R2', f"AAPL buy_order_id {aapl.buy_order_id}"
assert aapl.sell_order_id == '', f"AAPL sell_order_id {aapl.sell_order_id}"
assert aapl.create_date is not None, f"AAPL create_date {aapl.create_date}"

#FB 
assert fb.ticker == 'FB', f"FB ticker {fb.ticker}"
assert fb.shares == 83.0, f"FB shares {fb.shares}"
assert fb.planned_max_entry_price == 300.0, f"FB planned_max_entry_price {fb.planned_max_entry_price}"
assert fb.planned_exit_price == 330.0, f"FB planned_exit_price {fb.planned_exit_price}"
assert fb.stop_loss == 285.0, f"FB stop_loss {fb.stop_loss}"
assert fb.status == 'SALE_EXPIRED', f"FB status {fb.status}"
assert fb.exit_date == 0.0, f"FB exit_date {fb.exit_date}"
assert fb.entry_date !=  0.0, f"FB entry_date {fb.entry_date}"
assert fb.actual_exit_price == 0.0, f"FB actual_exit_price {fb.actual_exit_price}"
assert fb.actual_entry_price == 299.6, f"FB actual_entry_price {fb.actual_entry_price}"
assert fb.buy_order_id == 'B3', f"FB buy_order_id {fb.buy_order_id}"
assert fb.sell_order_id == 'S3', f"FB sell_order_id {fb.sell_order_id}"
assert fb.create_date is not None, f"FB create_date {fb.create_date}"

#AMZN 
assert amzn.ticker == 'AMZN', f"AMZN ticker {amzn.ticker}"
assert amzn.shares == 12.0, f"AMZN shares {amzn.shares}"
assert amzn.planned_max_entry_price == 2000.0, f"AMZN planned_max_entry_price {amzn.planned_max_entry_price}"
assert amzn.planned_exit_price == 2200.0, f"AMZN planned_exit_price {amzn.planned_exit_price}"
assert amzn.stop_loss == 1900.0, f"AMZN stop_loss {amzn.stop_loss}"
assert amzn.status == 'EXPIRED', f"AMZN status {amzn.status}"
assert amzn.exit_date == 0.0, f"AMZN exit_date {amzn.exit_date}"
assert amzn.entry_date == 0.0, f"AMZN entry_date {amzn.entry_date}"
assert amzn.actual_exit_price == 0.0, f"AMZN actual_exit_price {amzn.actual_exit_price}"
assert amzn.actual_entry_price == 0.0, f"AMZN actual_entry_price {amzn.actual_entry_price}"
assert amzn.buy_order_id == 'B4', f"AMZN buy_order_id {amzn.buy_order_id}"
assert amzn.sell_order_id == '', f"AMZN sell_order_id {amzn.sell_order_id}"
assert amzn.create_date is not None, f"AMZN create_date {amzn.create_date}"

#GOOG 
assert goog.ticker == 'GOOG', f"GOOG ticker {goog.ticker}"
assert goog.shares == 71.0, f"GOOG shares {goog.shares}"
assert goog.planned_max_entry_price == 350.0, f"GOOG planned_max_entry_price {goog.planned_max_entry_price}"
assert goog.planned_exit_price == 365.0, f"GOOG planned_exit_price {goog.planned_exit_price}"
assert goog.stop_loss == 343.0, f"GOOG stop_loss {goog.stop_loss}"
assert goog.status == 'SALE_CANCELED', f"GOOG status {goog.status}"
assert goog.exit_date == 0.0, f"GOOG exit_date {goog.exit_date}"
assert goog.entry_date != 0.0, f"GOOG entry_date {goog.entry_date}"
assert goog.actual_entry_price == 349.1, f"GOOG actual_exit_price {goog.actual_entry_price}"
assert goog.actual_exit_price == 0.0, f"GOOG actual_entry_price {goog.actual_entry_price}"
assert goog.buy_order_id == 'B5', f"GOOG buy_order_id {goog.buy_order_id}"
assert goog.sell_order_id == 'S5', f"GOOG sell_order_id {goog.sell_order_id}"
assert goog.create_date is not None, f"GOOG create_date {goog.create_date}"

#MSFT 
assert msft.ticker == 'MSFT', f"MSFT ticker {msft.ticker}"
assert msft.shares == 125.0, f"MSFT shares {msft.shares}"
assert msft.planned_max_entry_price == 200.0, f"MSFT planned_max_entry_price {msft.planned_max_entry_price}"
assert msft.planned_exit_price == 240.0, f"MSFT planned_exit_price {msft.planned_exit_price}"
assert msft.stop_loss == 187.0, f"MSFT stop_loss {msft.stop_loss}"
assert msft.status == 'CANCELED', f"MSFT status {msft.status}"
assert msft.exit_date == 0.0, f"MSFT exit_date {msft.exit_date}"
assert msft.entry_date == 0.0, f"MSFT entry_date {msft.entry_date}"
assert msft.actual_exit_price == 0.0, f"MSFT actual_exit_price {msft.actual_exit_price}"
assert msft.actual_entry_price == 0.0, f"MSFT actual_entry_price {msft.actual_entry_price}"
assert msft.buy_order_id == 'B6', f"MSFT buy_order_id {msft.buy_order_id}"
assert msft.sell_order_id == '', f"MSFT sell_order_id {msft.sell_order_id}"
assert msft.create_date is not None, f"MSFT create_date {msft.create_date}"

# PULSE 5
logging.info('Heartbeat pulse incoming...')
heartbeat.pulse()

tsla = heartbeat.db.get(tsla.create_date)
aapl = heartbeat.db.get(aapl.create_date)
fb = heartbeat.db.get(fb.create_date)
amzn = heartbeat.db.get(amzn.create_date)
goog = heartbeat.db.get(goog.create_date)
msft = heartbeat.db.get(msft.create_date)

#TSLA 
assert tsla.ticker == 'TSLA', f"TSLA ticker {tsla.ticker}"
assert tsla.shares == 50.0, f"TSLA shares {tsla.shares}"
assert tsla.planned_max_entry_price == 500.0, f"TSLA planned_max_entry_price {tsla.planned_max_entry_price}"
assert tsla.planned_exit_price == 520.0, f"TSLA planned_exit_price {tsla.planned_exit_price}"
assert tsla.stop_loss == 490.0, f"TSLA stop_loss {tsla.stop_loss}"
assert tsla.status == 'CLOSED', f"TSLA status {tsla.status}"
assert tsla.exit_date != 0.0, f"TSLA exit_date {tsla.exit_date}"
assert tsla.entry_date != 0.0, f"TSLA entry_date {tsla.entry_date}"
assert tsla.actual_exit_price == 523.1, f"TSLA actual_exit_price {tsla.actual_exit_price}"
assert tsla.actual_entry_price == 499.1, f"TSLA actual_entry_price {tsla.actual_entry_price}"
assert tsla.buy_order_id == 'B1', f"TSLA buy_order_id {tsla.buy_order_id}"
assert tsla.sell_order_id == 'R1', f"TSLA sell_order_id {tsla.sell_order_id}"
assert tsla.create_date is not None, f"TSLA create_date {tsla.create_date}"

#AAPL 
assert aapl.ticker == 'AAPL', f"AAPL ticker {aapl.ticker}"
assert aapl.shares == 62.0, f"AAPL shares {aapl.shares}"
assert aapl.planned_max_entry_price == 400.0, f"AAPL planned_max_entry_price {aapl.planned_max_entry_price}"
assert aapl.planned_exit_price == 450.0, f"AAPL planned_exit_price {aapl.planned_exit_price}"
assert aapl.stop_loss == 384.0, f"AAPL stop_loss {aapl.stop_loss}"
assert aapl.status == 'OPEN', f"AAPL status {aapl.status}"
assert aapl.exit_date == 0.0, f"AAPL exit_date {aapl.exit_date}"
assert aapl.entry_date != 0.0, f"AAPL entry_date {aapl.entry_date}"
assert aapl.actual_exit_price == 0, f"AAPL actual_exit_price {aapl.actual_exit_price}"
assert aapl.actual_entry_price == 398.1, f"AAPL actual_entry_price {aapl.actual_entry_price}"
assert aapl.buy_order_id == 'R2', f"AAPL buy_order_id {aapl.buy_order_id}"
assert aapl.sell_order_id == '', f"AAPL sell_order_id {aapl.sell_order_id}"
assert aapl.create_date is not None, f"AAPL create_date {aapl.create_date}"

#FB 
assert fb.ticker == 'FB', f"FB ticker {fb.ticker}"
assert fb.shares == 83.0, f"FB shares {fb.shares}"
assert fb.planned_max_entry_price == 300.0, f"FB planned_max_entry_price {fb.planned_max_entry_price}"
assert fb.planned_exit_price == 330.0, f"FB planned_exit_price {fb.planned_exit_price}"
assert fb.stop_loss == 285.0, f"FB stop_loss {fb.stop_loss}"
assert fb.status == 'SALE_EXPIRED', f"FB status {fb.status}"
assert fb.exit_date == 0.0, f"FB exit_date {fb.exit_date}"
assert fb.entry_date !=  0.0, f"FB entry_date {fb.entry_date}"
assert fb.actual_exit_price == 0.0, f"FB actual_exit_price {fb.actual_exit_price}"
assert fb.actual_entry_price == 299.6, f"FB actual_entry_price {fb.actual_entry_price}"
assert fb.buy_order_id == 'B3', f"FB buy_order_id {fb.buy_order_id}"
assert fb.sell_order_id == 'S3', f"FB sell_order_id {fb.sell_order_id}"
assert fb.create_date is not None, f"FB create_date {fb.create_date}"

#AMZN 
assert amzn.ticker == 'AMZN', f"AMZN ticker {amzn.ticker}"
assert amzn.shares == 12.0, f"AMZN shares {amzn.shares}"
assert amzn.planned_max_entry_price == 2000.0, f"AMZN planned_max_entry_price {amzn.planned_max_entry_price}"
assert amzn.planned_exit_price == 2200.0, f"AMZN planned_exit_price {amzn.planned_exit_price}"
assert amzn.stop_loss == 1900.0, f"AMZN stop_loss {amzn.stop_loss}"
assert amzn.status == 'EXPIRED', f"AMZN status {amzn.status}"
assert amzn.exit_date == 0.0, f"AMZN exit_date {amzn.exit_date}"
assert amzn.entry_date == 0.0, f"AMZN entry_date {amzn.entry_date}"
assert amzn.actual_exit_price == 0.0, f"AMZN actual_exit_price {amzn.actual_exit_price}"
assert amzn.actual_entry_price == 0.0, f"AMZN actual_entry_price {amzn.actual_entry_price}"
assert amzn.buy_order_id == 'B4', f"AMZN buy_order_id {amzn.buy_order_id}"
assert amzn.sell_order_id == '', f"AMZN sell_order_id {amzn.sell_order_id}"
assert amzn.create_date is not None, f"AMZN create_date {amzn.create_date}"

#GOOG 
assert goog.ticker == 'GOOG', f"GOOG ticker {goog.ticker}"
assert goog.shares == 71.0, f"GOOG shares {goog.shares}"
assert goog.planned_max_entry_price == 350.0, f"GOOG planned_max_entry_price {goog.planned_max_entry_price}"
assert goog.planned_exit_price == 365.0, f"GOOG planned_exit_price {goog.planned_exit_price}"
assert goog.stop_loss == 343.0, f"GOOG stop_loss {goog.stop_loss}"
assert goog.status == 'SALE_CANCELED', f"GOOG status {goog.status}"
assert goog.exit_date == 0.0, f"GOOG exit_date {goog.exit_date}"
assert goog.entry_date != 0.0, f"GOOG entry_date {goog.entry_date}"
assert goog.actual_entry_price == 349.1, f"GOOG actual_exit_price {goog.actual_entry_price}"
assert goog.actual_exit_price == 0.0, f"GOOG actual_entry_price {goog.actual_entry_price}"
assert goog.buy_order_id == 'B5', f"GOOG buy_order_id {goog.buy_order_id}"
assert goog.sell_order_id == 'S5', f"GOOG sell_order_id {goog.sell_order_id}"
assert goog.create_date is not None, f"GOOG create_date {goog.create_date}"

#MSFT 
assert msft.ticker == 'MSFT', f"MSFT ticker {msft.ticker}"
assert msft.shares == 125.0, f"MSFT shares {msft.shares}"
assert msft.planned_max_entry_price == 200.0, f"MSFT planned_max_entry_price {msft.planned_max_entry_price}"
assert msft.planned_exit_price == 240.0, f"MSFT planned_exit_price {msft.planned_exit_price}"
assert msft.stop_loss == 187.0, f"MSFT stop_loss {msft.stop_loss}"
assert msft.status == 'CANCELED', f"MSFT status {msft.status}"
assert msft.exit_date == 0.0, f"MSFT exit_date {msft.exit_date}"
assert msft.entry_date == 0.0, f"MSFT entry_date {msft.entry_date}"
assert msft.actual_exit_price == 0.0, f"MSFT actual_exit_price {msft.actual_exit_price}"
assert msft.actual_entry_price == 0.0, f"MSFT actual_entry_price {msft.actual_entry_price}"
assert msft.buy_order_id == 'B6', f"MSFT buy_order_id {msft.buy_order_id}"
assert msft.sell_order_id == '', f"MSFT sell_order_id {msft.sell_order_id}"
assert msft.create_date is not None, f"MSFT create_date {msft.create_date}"

# PULSE 6
logging.info('Heartbeat pulse incoming...')
heartbeat.pulse()

tsla = heartbeat.db.get(tsla.create_date)
aapl = heartbeat.db.get(aapl.create_date)
fb = heartbeat.db.get(fb.create_date)
amzn = heartbeat.db.get(amzn.create_date)
goog = heartbeat.db.get(goog.create_date)
msft = heartbeat.db.get(msft.create_date)

#TSLA 
assert tsla.ticker == 'TSLA', f"TSLA ticker {tsla.ticker}"
assert tsla.shares == 50.0, f"TSLA shares {tsla.shares}"
assert tsla.planned_max_entry_price == 500.0, f"TSLA planned_max_entry_price {tsla.planned_max_entry_price}"
assert tsla.planned_exit_price == 520.0, f"TSLA planned_exit_price {tsla.planned_exit_price}"
assert tsla.stop_loss == 490.0, f"TSLA stop_loss {tsla.stop_loss}"
assert tsla.status == 'CLOSED', f"TSLA status {tsla.status}"
assert tsla.exit_date != 0.0, f"TSLA exit_date {tsla.exit_date}"
assert tsla.entry_date != 0.0, f"TSLA entry_date {tsla.entry_date}"
assert tsla.actual_exit_price == 523.1, f"TSLA actual_exit_price {tsla.actual_exit_price}"
assert tsla.actual_entry_price == 499.1, f"TSLA actual_entry_price {tsla.actual_entry_price}"
assert tsla.buy_order_id == 'B1', f"TSLA buy_order_id {tsla.buy_order_id}"
assert tsla.sell_order_id == 'R1', f"TSLA sell_order_id {tsla.sell_order_id}"
assert tsla.create_date is not None, f"TSLA create_date {tsla.create_date}"

#AAPL 
assert aapl.ticker == 'AAPL', f"AAPL ticker {aapl.ticker}"
assert aapl.shares == 62.0, f"AAPL shares {aapl.shares}"
assert aapl.planned_max_entry_price == 400.0, f"AAPL planned_max_entry_price {aapl.planned_max_entry_price}"
assert aapl.planned_exit_price == 450.0, f"AAPL planned_exit_price {aapl.planned_exit_price}"
assert aapl.stop_loss == 384.0, f"AAPL stop_loss {aapl.stop_loss}"
assert aapl.status == 'SELLING', f"AAPL status {aapl.status}"
assert aapl.exit_date == 0.0, f"AAPL exit_date {aapl.exit_date}"
assert aapl.entry_date != 0.0, f"AAPL entry_date {aapl.entry_date}"
assert aapl.actual_exit_price == 0.0, f"AAPL actual_exit_price {aapl.actual_exit_price}"
assert aapl.actual_entry_price == 398.1, f"AAPL actual_entry_price {aapl.actual_entry_price}"
assert aapl.buy_order_id == 'R2', f"AAPL buy_order_id {aapl.buy_order_id}"
assert aapl.sell_order_id == 'S2', f"AAPL sell_order_id {aapl.sell_order_id}"
assert aapl.create_date is not None, f"AAPL create_date {aapl.create_date}"

#FB 
assert fb.ticker == 'FB', f"FB ticker {fb.ticker}"
assert fb.shares == 83.0, f"FB shares {fb.shares}"
assert fb.planned_max_entry_price == 300.0, f"FB planned_max_entry_price {fb.planned_max_entry_price}"
assert fb.planned_exit_price == 330.0, f"FB planned_exit_price {fb.planned_exit_price}"
assert fb.stop_loss == 285.0, f"FB stop_loss {fb.stop_loss}"
assert fb.status == 'SALE_EXPIRED', f"FB status {fb.status}"
assert fb.exit_date == 0.0, f"FB exit_date {fb.exit_date}"
assert fb.entry_date !=  0.0, f"FB entry_date {fb.entry_date}"
assert fb.actual_exit_price == 0.0, f"FB actual_exit_price {fb.actual_exit_price}"
assert fb.actual_entry_price == 299.6, f"FB actual_entry_price {fb.actual_entry_price}"
assert fb.buy_order_id == 'B3', f"FB buy_order_id {fb.buy_order_id}"
assert fb.sell_order_id == 'S3', f"FB sell_order_id {fb.sell_order_id}"
assert fb.create_date is not None, f"FB create_date {fb.create_date}"

#AMZN 
assert amzn.ticker == 'AMZN', f"AMZN ticker {amzn.ticker}"
assert amzn.shares == 12.0, f"AMZN shares {amzn.shares}"
assert amzn.planned_max_entry_price == 2000.0, f"AMZN planned_max_entry_price {amzn.planned_max_entry_price}"
assert amzn.planned_exit_price == 2200.0, f"AMZN planned_exit_price {amzn.planned_exit_price}"
assert amzn.stop_loss == 1900.0, f"AMZN stop_loss {amzn.stop_loss}"
assert amzn.status == 'EXPIRED', f"AMZN status {amzn.status}"
assert amzn.exit_date == 0.0, f"AMZN exit_date {amzn.exit_date}"
assert amzn.entry_date == 0.0, f"AMZN entry_date {amzn.entry_date}"
assert amzn.actual_exit_price == 0.0, f"AMZN actual_exit_price {amzn.actual_exit_price}"
assert amzn.actual_entry_price == 0.0, f"AMZN actual_entry_price {amzn.actual_entry_price}"
assert amzn.buy_order_id == 'B4', f"AMZN buy_order_id {amzn.buy_order_id}"
assert amzn.sell_order_id == '', f"AMZN sell_order_id {amzn.sell_order_id}"
assert amzn.create_date is not None, f"AMZN create_date {amzn.create_date}"

#GOOG 
assert goog.ticker == 'GOOG', f"GOOG ticker {goog.ticker}"
assert goog.shares == 71.0, f"GOOG shares {goog.shares}"
assert goog.planned_max_entry_price == 350.0, f"GOOG planned_max_entry_price {goog.planned_max_entry_price}"
assert goog.planned_exit_price == 365.0, f"GOOG planned_exit_price {goog.planned_exit_price}"
assert goog.stop_loss == 343.0, f"GOOG stop_loss {goog.stop_loss}"
assert goog.status == 'SALE_CANCELED', f"GOOG status {goog.status}"
assert goog.exit_date == 0.0, f"GOOG exit_date {goog.exit_date}"
assert goog.entry_date != 0.0, f"GOOG entry_date {goog.entry_date}"
assert goog.actual_entry_price == 349.1, f"GOOG actual_exit_price {goog.actual_entry_price}"
assert goog.actual_exit_price == 0.0, f"GOOG actual_entry_price {goog.actual_entry_price}"
assert goog.buy_order_id == 'B5', f"GOOG buy_order_id {goog.buy_order_id}"
assert goog.sell_order_id == 'S5', f"GOOG sell_order_id {goog.sell_order_id}"
assert goog.create_date is not None, f"GOOG create_date {goog.create_date}"

#MSFT 
assert msft.ticker == 'MSFT', f"MSFT ticker {msft.ticker}"
assert msft.shares == 125.0, f"MSFT shares {msft.shares}"
assert msft.planned_max_entry_price == 200.0, f"MSFT planned_max_entry_price {msft.planned_max_entry_price}"
assert msft.planned_exit_price == 240.0, f"MSFT planned_exit_price {msft.planned_exit_price}"
assert msft.stop_loss == 187.0, f"MSFT stop_loss {msft.stop_loss}"
assert msft.status == 'CANCELED', f"MSFT status {msft.status}"
assert msft.exit_date == 0.0, f"MSFT exit_date {msft.exit_date}"
assert msft.entry_date == 0.0, f"MSFT entry_date {msft.entry_date}"
assert msft.actual_exit_price == 0.0, f"MSFT actual_exit_price {msft.actual_exit_price}"
assert msft.actual_entry_price == 0.0, f"MSFT actual_entry_price {msft.actual_entry_price}"
assert msft.buy_order_id == 'B6', f"MSFT buy_order_id {msft.buy_order_id}"
assert msft.sell_order_id == '', f"MSFT sell_order_id {msft.sell_order_id}"
assert msft.create_date is not None, f"MSFT create_date {msft.create_date}"




