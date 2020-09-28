import logging
import bot_configuration
import heartbeat

#One of the main entry points for starting the bot. This script will fire the pulse once and then, finish. 
#Any data stored in the objects in the heartbeat's closures will be lost unless persisted in a data source.

logging.basicConfig(format=bot_configuration.LOG_FORMAT, filename=bot_configuration.DATA_FOLDER+bot_configuration.LOG_FILE,level=bot_configuration.LOGGING_LEVEL)

console = logging.StreamHandler()
console.setLevel(bot_configuration.LOGGING_LEVEL)
formatter = logging.Formatter(bot_configuration.LOG_FORMAT)
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logging.getLogger("stockstats").setLevel(logging.ERROR)

heartbeat.pulse()