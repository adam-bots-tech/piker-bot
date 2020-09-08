#Create a copy called 'bot_configuration.py' to be used as a module by the bot
import logging

#For Desktop
#DATA_FOLDER ='D:\\development\\docker-data\\'
#For Docker
DATA_FOLDER='/var/lib/piker-bot/'
DATABASE_NAME='piker-bot.db'
TRAILING_STOP_LOSS=0.02
LOGGING_LEVEL=logging.DEBUG
LOG_FILE='piker-bot.log'
LOG_FORMAT='%(asctime)s:%(levelname)s:%(message)s'
MAX_TRADES_OPEN=50
MAX_DAYS_TO_KEEP_TRADE_QUEUED=1
PERCENTAGE_OF_ACCOUNT_TO_LEVERAGE=0.05
MIN_AMOUNT_PER_TRADE=100.0
#Go here to sign up and get your api keys
#https://alpaca.markets/
ALPACA_KEY_ID='<KEY_ID_HERE>'
ALPACA_SECRET_KEY='<SECRET_KEY_HERE>'
ALPACA_PAPER_TRADING_ON=True
TRADE_JOURNAL_TITLE='Stock Trading Journal'