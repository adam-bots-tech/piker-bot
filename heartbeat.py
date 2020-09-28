import state_db
import brokerage
import logging
import trades_manager
import trades_db
import time
import requests
import trade_journal
import bot_configuration
import stock_math

# We trap references to objects as part of a closure for the main-schedule.py, so we can persist state in between pulses. Has no effect on the main-pulse.py script.
# Need to be careful what you store in these objects as unbounded lists can cause memory leaks.
# Also important to not attempt to connect to any of the underlying data sources in a constructor using this approach. We do it using bootstrap methods when the pulse actually fires.
s = state_db.StateDB(bot_configuration.DATA_FOLDER + bot_configuration.DATABASE_NAME)
b = brokerage.Brokerage(bot_configuration.ALPACA_PAPER_TRADING_ON, bot_configuration.ALPACA_KEY_ID, bot_configuration.ALPACA_SECRET_KEY, bot_configuration.DATA_FOLDER)
j = trade_journal.TradeJournal(bot_configuration.TRADE_JOURNAL_TITLE)
db = trades_db.DB(j, bot_configuration.DATA_FOLDER + bot_configuration.DATABASE_NAME)
sm = stock_math.StockMath()

#This method brings the bot to life and causes it to perform it's repeated actions at an interval defined by the scripts calling it.
#It's important to think about how we assign variables when working with a function like this. 
#We only store persistant data inside the objects bound to our closure; everything else should be a variable bound to the function's scope, so it's memory is released when the function finishes calling.
def pulse():
	try:

		# Pre-workflow: Check to see if the user has added new trades to the trade journal
		trades_manager.pull_queued_trades(db, j)
		
		is_open = b.is_open()
		#is_open = True

		logging.info(f'Heartbeat Pulse {time.time()}: Market Open - {is_open}')

		# Log a message about the market opening or closing the first time we detect a change in the state.
		if (is_open == None):
			logging.error('Brokerage API failed to return market status.')
			return
		elif is_open == False:
			if s.get_market_open() == True:
				logging.critical('Market has closed.')
				s.set_market_open(False)
			return

		if s.get_market_open() == False:
			s.set_market_open(True)
			logging.critical('Market has opened')

		# Step one: Expire any expired queued trades in the database, so we don't run them in later steps.
		trades_manager.expire_trades(b, db)
		# Step two: Update the database and trade journal for trades with open buy orders
		trades_manager.handle_open_buy_orders(b, db, s)
		# Step three: Update the database and trade journal for trades with open sell orders
		trades_manager.handle_open_sell_orders(b, db, s)
		# Step four: Check the status on positions we already have and sell if the correct conditions have been met.
		trades_manager.handle_open_trades(b, db, s, sm)
		# Step five: If we are able to open new trades for the day, check the status on tickers for trades in the queue and purchase shares if the correct conditions have been met.
		trades_manager.open_new_trades(b, db, s, sm)


	# We wrap all of the pulse logic in a try catch statement, because we never want an exception to kill the heartbeat. Bots never die.
	except requests.exceptions.ConnectionError as conn:
		logging.error(f'Bad connection. {str(conn)}')

	except Exception as err:
		logging.error('Exception occured during heartbeat:', exc_info=err)
