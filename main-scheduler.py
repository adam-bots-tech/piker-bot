import schedule
import logging
import bot_configuration
import time
import heartbeat

#One of the main entry points for starting the bot. This script will fire the pulse once every minute until the script is manually killed.
#Any data stored in the objects in the heartbeat's closures will be persisted in memory in between pulses.

logging.basicConfig(format=bot_configuration.LOG_FORMAT, filename=bot_configuration.DATA_FOLDER+bot_configuration.LOG_FILE,level=bot_configuration.LOGGING_LEVEL)

console = logging.StreamHandler()
console.setLevel(bot_configuration.LOGGING_LEVEL)
formatter = logging.Formatter(bot_configuration.LOG_FORMAT)
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logging.getLogger("schedule").setLevel(logging.ERROR)
logging.getLogger("stockstats").setLevel(logging.ERROR)

#Configure the heartbeat
schedule.every(1).minutes.do(heartbeat.pulse)

logging.critical('Bot is online.')

#Pulse forever
while True:
	schedule.run_pending()
	time.sleep(1)