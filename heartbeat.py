import state
import brokerage
import logging
import trades_manager
import trades_db

#Override with a sub class in tests
state = state.State()

#Override with a sub class in tests
b = brokerage.Brokerage()

db = trades_db.DB()

def pulse():
	try:
		is_open = b.is_open()

		if (is_open == None):
			logging.error('Brokerage API failed to return market status.')
			return
		elif is_open == False:
			if state.market_open == True:
				logging.info('Market has closed.')
				state.market_open = False
			return

		if state.market_open == False:
			state.market_open = True;
			logging.info('Market has opened')

		trades_manager.expire_trades(b, db)
		trades_manager.handle_open_buy_orders(b, db)
		trades_manager.handle_open_sell_orders(b, db)
		trades_manager.handle_open_trades(b, db)
		trades_manager.open_new_trades(b, db)
	except Exception as err:
		logging.error('Exception occured during heartbeat:', exc_info=err)