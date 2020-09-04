import logging
import bot_configuration
import heartbeat

logging.basicConfig(format=bot_configuration.LOG_FORMAT, filename=bot_configuration.DATA_FOLDER+bot_configuration.LOG_FILE,level=bot_configuration.LOGGING_LEVEL)

console = logging.StreamHandler()
console.setLevel(bot_configuration.LOGGING_LEVEL)
formatter = logging.Formatter(bot_configuration.LOG_FORMAT)
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

heartbeat.pulse()