import schedule
import logging
import bot_configuration
import trades_manager
import brokerage
import time

logging.basicConfig(filename=bot_configuration.DATA_FOLDER+bot_configuration.LOG_FILE,level=bot_configuration.LOGGING_LEVEL)
brokerage_open = False

def main():
	print('Im working')
	if brokerage.is_open() == False:
		if brokerage_open == True:
			logging.info('Market has closed.')
			brokerage_open = False
		return

	if brokerage_open == False:
		brokerage_open = True;
		logging.info('Market has opened')

	trades_manager.handle_open_trades()
	trades_manager.open_new_trades()

schedule.every(1).minutes.do(main)

while True:
	schedule.run_pending()
	time.sleep(1)