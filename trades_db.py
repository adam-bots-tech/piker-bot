import sqlite3
import bot_configuration
from datetime import datetime
from trade import Trade

def help():
	print('create_new_long_trade(ticker, entry, exit, stop_loss)')

def create_new_long_trade(ticker, entry, exit, stop_loss):
	db = DB()
	db.add(db.generate_default_trade(ticker, 'long', entry, exit, stop_loss))

class DB:
	def __connect__(self):
		return sqlite3.connect(bot_configuration.DATA_FOLDER + bot_configuration.DATABASE_NAME)

	def __create_table__(self, c):
		c.execute('''CREATE TABLE IF NOT EXISTS trades (create_date REAL PRIMARY KEY, ticker TEXT, entry_date REAL, exit_date REAL, shares REAL, 
			planned_exit_price REAL, planned_entry_price REAL, stop_loss REAL, actual_exit_price REAL, actual_entry_price REAL, status TEXT, buy_order_id TEXT,
			sell_order_id TEXT, type TEXT)''')

	def generate_default_trade(self, ticker, type, entry, exit, stop_loss):
		return Trade(datetime.timestamp(datetime.now()), ticker, 0.0, 0.0, 0.0, exit, entry, stop_loss, 0.0, 0.0, 'QUEUED', '', '', type)

	def get(self, create_date):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f'SELECT * FROM trades WHERE create_date={create_date}')
		data = c.fetchone()
		conn.close()
		if (data == None):
			return None
		else:
			return Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13])


	def add(self, trade):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f'''INSERT INTO trades VALUES ({trade.create_date}, '{trade.ticker}', {trade.entry_date}, {trade.exit_date}, 
			{trade.shares}, {trade.planned_exit_price}, {trade.planned_entry_price}, {trade.stop_loss}, {trade.actual_exit_price}, 
			{trade.actual_entry_price}, '{trade.status}', '{trade.buy_order_id}', '{trade.sell_order_id}', '{trade.type}')''')
		conn.commit()
		conn.close()
		return trade

	def create_new_long_trade(self, ticker, entry, exit, stop_loss):
		self.add(self.generate_default_trade(ticker, 'long', entry, exit, stop_loss))

	def open(self, create_date, shares, price):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'OPEN', shares = {shares}, actual_entry_price = {price}, entry_date = {datetime.timestamp(datetime.now())} WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def close(self, create_date, price):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'CLOSED', actual_exit_price = {price}, exit_date = {datetime.timestamp(datetime.now())} WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def cancel(self, create_date):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'CANCELED' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def cancel_sale(self, create_date):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'SALE_CANCELED' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def invalidate(self, create_date):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'MISSING' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def out_of_money(self, create_date):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'FUNDS_TOO_LOW' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def sell(self, create_date, order_id):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'SELLING', sell_order_id = '{order_id}' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def buy(self, create_date, shares, order_id):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'BUYING', shares = {shares}, buy_order_id = '{order_id}' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def replace_buy(self, create_date, order_id):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET buy_order_id = '{order_id}' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def replace_sale(self, create_date, order_id):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET sell_order_id = '{order_id}' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def expire(self, create_date):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'EXPIRED' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def expire_sale(self, create_date):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET status = 'SALE_EXPIRED' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def sync(self, create_date, position):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET shares = '{position.shares}', actual_entry_price = '{position.price}' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def update_stop_loss(self, create_date, stop_loss):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		c.execute(f"UPDATE trades SET stop_loss = '{stop_loss}' WHERE create_date = {create_date}")
		conn.commit()
		conn.close()

	def get_all_trades(self):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		trades = []

		for data in c.execute('SELECT * FROM trades ORDER BY create_date'):
			trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13]))

		conn.close()
		return trades

	def get_open_long_trades(self):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		trades = []

		for data in c.execute("SELECT * FROM trades WHERE status = 'OPEN' AND type = 'long' ORDER BY create_date ASC"):
			trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13]))

		conn.close()
		return trades

	def get_trades_being_bought(self):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		trades = []

		for data in c.execute("SELECT * FROM trades WHERE status = 'BUYING' ORDER BY create_date ASC"):
			trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13]))

		conn.close()
		return trades

	def get_trades_being_sold(self):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		trades = []

		for data in c.execute("SELECT * FROM trades WHERE status = 'SELLING' ORDER BY create_date ASC"):
			trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13]))

		conn.close()
		return trades

	def get_active_trades(self):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		trades = []

		for data in c.execute("SELECT * FROM trades WHERE status = 'OPEN' OR status = 'BUYING' OR status = 'SELLING' ORDER BY create_date ASC"):
			trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13]))

		conn.close()
		return trades

	def get_queued_trades(self):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		trades = []

		for data in c.execute("SELECT * FROM trades WHERE status = 'QUEUED' ORDER BY create_date ASC"):
			trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13]))

		conn.close()
		return trades

	def get_queued_long_trades(self):
		conn = self.__connect__()
		c = conn.cursor()
		self.__create_table__(c)
		trades = []

		for data in c.execute("SELECT * FROM trades WHERE status = 'QUEUED' AND type = 'long' ORDER BY create_date ASC"):
			trades.append(Trade(data[0],data[1],data[2],data[3],data[4],data[5],data[6],data[7],data[8],data[9],data[10],data[11],data[12],data[13]))

		conn.close()
		return trades