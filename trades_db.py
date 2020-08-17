import sqlite3
import bot_configuration
import time

class Trade:

	def __init__(self, create_date, ticker, entry_date, exit_date, shares, exit, entry, stop_loss, actual_exit_price, actual_entry_price, status):
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

def __connect__():
	return sqlite3.connect(bot_configuration.DATA_FOLDER + bot_configuration.DATABASE_NAME)

def __create_table__(c):
	c.execute('''CREATE TABLE IF NOT EXISTS trades (create_date REAL PRIMARY KEY, ticker TEXT, entry_date REAL, exit_date REAL, shares REAL, 
		planned_exit_price REAL, planned_entry_price REAL, stop_loss REAL, actual_exit_price REAL, actual_entry_price REAL, status TEXT)''')

def generate_default_trade(ticker, shares, entry, exit):
	return Trade(time.time(), ticker, 0.0, 0.0, shares, exit, entry, 0.0, 0.0, 0.0, 'QUEUED')

def get(create_date):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f'SELECT * FROM trades WHERE create_date={create_date}')
	data = c.fetchone()
	conn.close()
	if (data == None):
		return None
	else:
		return Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10])


def add(trade):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f'''INSERT INTO trades VALUES ({trade.create_date}, '{trade.ticker}', {trade.entry_date}, {trade.exit_date}, 
		{trade.shares}, {trade.planned_exit_price}, {trade.planned_entry_price}, {trade.stop_loss}, {trade.actual_exit_price}, {trade.actual_entry_price}, '{trade.status}')''')
	conn.commit()
	conn.close()
	return trade

def cancel(create_date):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f"UPDATE trades SET status = 'CANCELLED' WHERE create_date = {create_date}")
	conn.commit()
	conn.close()

def invalidate(create_date):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f"UPDATE trades SET status = 'MISSING' WHERE create_date = {create_date}")
	conn.commit()
	conn.close()

def sell(create_date):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f"UPDATE trades SET status = 'SELLING' WHERE create_date = {create_date}")
	conn.commit()
	conn.close()

def buy(create_date):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f"UPDATE trades SET status = 'BUYING' WHERE create_date = {create_date}")
	conn.commit()
	conn.close()

def expire(create_date):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f"UPDATE trades SET status = 'EXPIRED' WHERE create_date = {create_date}")
	conn.commit()
	conn.close()

def sync(create_date, position):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f"UPDATE trades SET shares = '{position.shares}', actual_entry_price = '{position.price}' WHERE create_date = {create_date}")
	conn.commit()
	conn.close()

def update_stop_loss(create_date, stop_loss):
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	c.execute(f"UPDATE trades SET stop_loss = '{stop_loss}' WHERE create_date = {create_date}")
	conn.commit()
	conn.close()

def get_all_trades():
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	trades = []

	for data in c.execute('SELECT * FROM trades ORDER BY create_date'):
		trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10]))

	conn.close()
	return trades

def get_open_trades():
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	trades = []

	for data in c.execute("SELECT * FROM trades WHERE status = 'OPEN' ORDER BY create_date ASC"):
		trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10]))

	conn.close()
	return trades

def get_queued_trades():
	conn = __connect__()
	c = conn.cursor()
	__create_table__(c)
	trades = []

	for data in c.execute("SELECT * FROM trades WHERE status = 'QUEUED' ORDER BY create_date ASC"):
		trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10]))

	conn.close()
	return trades