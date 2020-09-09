import state_db
import brokerage
import logging
import trades_manager
import trades_db
import time
import requests
import trade_journal
import bot_configuration

#Override with a sub class in tests
s = state_db.StateDB(bot_configuration.DATA_FOLDER + bot_configuration.DATABASE_NAME)

#Override with a sub class in tests
b = brokerage.Brokerage(bot_configuration.ALPACA_PAPER_TRADING_ON, bot_configuration.ALPACA_KEY_ID, bot_configuration.ALPACA_SECRET_KEY)

j = trade_journal.TradeJournal(bot_configuration.TRADE_JOURNAL_TITLE)

db = trades_db.DB(j, bot_configuration.DATA_FOLDER + bot_configuration.DATABASE_NAME)

def pulse():
	try:
		j.bootstrap()

		is_open = b.is_open()
		#is_open = True

		logging.info(f'Heartbeat Pulse {time.time()}: Market Open - {is_open}')

		if (is_open == None):
			logging.error('Brokerage API failed to return market status.')
			return
		elif is_open == False:
			if s.get_market_open() == True:
				pull_queued_trades()
				logging.info('Market has closed.')
				s.set_market_open(False)
			return

		if s.get_market_open() == False:
			pull_queued_trades()
			s.set_market_open(True)
			logging.info('Market has opened')

		trades_manager.expire_trades(b, db)
		trades_manager.handle_open_buy_orders(b, db)
		trades_manager.handle_open_sell_orders(b, db)
		trades_manager.handle_open_trades(b, db, s)
		trades_manager.open_new_trades(b, db, s)
	except requests.exceptions.ConnectionError as conn:
		logging.info(f'Bad connection. {conn.message}')
	except Exception as err:
		logging.error('Exception occured during heartbeat:', exc_info=err)

def pull_queued_trades():
	j.bootstrap()
	rows = j.get_queued_trades()
	header_row = rows[0]

	for row in rows:
		if row[0] == '' or row[0].lower() == 'ticker':
			continue

		trade = db.create_new_long_trade(row[0], row[2], row[3], row[4], row[6])
		j.create_trade_record(trade, row[5], row[7], row[8])
		logging.info(f'Trade added to Queue: [{row[0]}, long, {row[2]}, {row[3]}, {row[4]}]')

	j.reset_queued_trades(header_row)