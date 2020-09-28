#Create a copy called 'bot_configuration.py'
import logging

#Data folder is location on hard drive of bot's local database and log file
#For Desktop
#DATA_FOLDER ='D:\\development\\docker-data\\'
#For Docker
DATA_FOLDER='/var/lib/piker-bot/'

# Technical configuration
DATABASE_NAME='piker-bot.db'
LOGGING_LEVEL=logging.DEBUG
LOG_FILE='piker-bot.log'
LOG_FORMAT='%(asctime)s:%(levelname)s:%(message)s'

# Default Settings: We leverage 5% of the account with no less than $100 per trade.
PERCENTAGE_OF_ACCOUNT_TO_LEVERAGE=0.05
MIN_AMOUNT_PER_TRADE=100.0

#Go here to sign up and get your api keys
#https://alpaca.markets/
ALPACA_KEY_ID='<KEY_ID_HERE>'
ALPACA_SECRET_KEY='<SECRET_KEY_HERE>'
ALPACA_PAPER_TRADING_ON=True

#We find the trade journal in Google Drive based on it's title.
TRADE_JOURNAL_TITLE='Stock Trading Journal'