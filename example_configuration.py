#Create a copy called 'bot_configuration.py' to be used as a module by the bot
import logging

DATA_FOLDER ='D:\\development\\data\\'
DATABASE_NAME='piker-bot.db'
TRAILING_STOP_LOSS=0.02
LOGGING_LEVEL=logging.DEBUG
LOG_FILE='piker-bot.log'
LOG_FORMAT='%(asctime)s:%(levelname)s:%(message)s'
MAX_TRADES_OPEN=4
MAX_DAYS_TO_KEEP_TRADE_QUEUED=7
CONSOLE_LOGGING=True
PERCENTAGE_OF_ACCOUNT_TO_LEVERAGE=0.05
MIN_AMOUNT_PER_TRADE=100.0
ALPACA_KEY_ID='<KEY_ID_HERE>'
ALPACA_SECRET_KEY='<SECRET_KEY_HERE>'
ALPACA_PAPER_TRADING_ON=True