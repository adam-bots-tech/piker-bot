import schedule
import logging
import bot_configuration
import trades_manager
import brokerage
import time
import state

if bot_configuration.CONSOLE_LOGGING == True:
	logging.basicConfig(level=bot_configuration.LOGGING_LEVEL)
else:
	logging.basicConfig(filename=bot_configuration.DATA_FOLDER+bot_configuration.LOG_FILE,level=bot_configuration.LOGGING_LEVEL)

state = state.State()

def heartbeat():
	try:
		if brokerage.is_open() == False:
			if state.market_open == True:
				logging.info('Market has closed.')
				state.market_open = False
			return

		if state.market_open == False:
			state.market_open = True;
			logging.info('Market has opened')

		trades_manager.handle_open_trades()
		trades_manager.open_new_trades()
	except Exception as err:
		logging.error('Exception occured during heartbeat:', exc_info=err)

schedule.every(5).seconds.do(heartbeat)

while True:
	schedule.run_pending()
	time.sleep(1)