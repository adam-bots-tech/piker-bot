import state
import brokerage
import logging
import trades_manager
import trades_db
import time
import requests
import trade_journal

#Override with a sub class in tests
s = state.State()

#Override with a sub class in tests
b = brokerage.Brokerage()

j = trade_journal.TradeJournal()

db = trades_db.DB(j)

def pulse():
	try:

		if s.bootstrapped == False:
			j.bootstrap()
			rows = j.get_queued_trades()
			#Delete header row
			header_row = rows[0]
		
			for row in rows:
				if row[0] == '' or row[0].lower() == 'ticker':
					continue

				notes = row[5]
				trade = db.create_new_long_trade(row[0], row[2], row[3], row[4])
				j.create_trade_record(trade, notes)
				logging.info(f'Trade added to Queue: [{row[0]}, long, {row[2]}, {row[3]}, {row[4]}]')
 
			j.reset_queued_trades(header_row)
			s.bootstrapped = True


		is_open = b.is_open()

		logging.info(f'Heartbeat Pulse {time.time()}: Market Open - {is_open}')

		if (is_open == None):
			logging.error('Brokerage API failed to return market status.')
			return
		elif is_open == False:
			if s.market_open == True:
				logging.info('Market has closed.')
				s.market_open = False
				s.bootstrapped = False
			return

		if s.market_open == False:
			s.market_open = True;
			s.bootstrapped = False
			logging.info('Market has opened')

		trades_manager.expire_trades(b, db)
		trades_manager.handle_open_buy_orders(b, db)
		trades_manager.handle_open_sell_orders(b, db)
		trades_manager.handle_open_trades(b, db)
		trades_manager.open_new_trades(b, db)
	except requests.exceptions.ConnectionError as conn:
		logging.info(f'Bad connection. {conn.message}')
	except Exception as err:
		logging.error('Exception occured during heartbeat:', exc_info=err)