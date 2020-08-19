#Create a copy called 'bot_configuration.py' to be used as a module by the bot
import logging

DATA_FOLDER ='D:\\development\\data\\'
DATABASE_NAME='piker-bot.db'
RISK=1
REWARD=3
TRAILING_STOP_LOSS=0.02
LOGGING_LEVEL=logging.DEBUG
LOG_FILE='piker-bot.log'
LOG_FORMAT='%(asctime)s:%(levelname)s:%(message)s'
MAX_TRADES_OPEN=4
MAX_DAYS_TO_KEEP_TRADE_QUEUED=7
CONSOLE_LOGGING=True