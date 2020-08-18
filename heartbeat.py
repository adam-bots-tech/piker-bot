import state
import brokerage
import logging
import trades_manager

#Override with a sub class in tests
state = state.State()

#Override with a sub class in tests
b = brokerage.Brokerage()

def pulse():
	try:
		if b.is_open() == False:
			if state.market_open == True:
				logging.info('Market has closed.')
				state.market_open = False
			return

		if state.market_open == False:
			state.market_open = True;
			logging.info('Market has opened')

		trades_manager.expire_trades(b)
		trades_manager.handle_open_buy_orders(b)
		trades_manager.handle_open_sell_orders(b)
		trades_manager.handle_open_trades(b)
		trades_manager.open_new_trades(b)
	except Exception as err:
		logging.error('Exception occured during heartbeat:', exc_info=err)