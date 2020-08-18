import schedule
import logging
import bot_configuration
import time
import heartbeat

#Adjust the logging based on mode
if bot_configuration.CONSOLE_LOGGING == True:
	logging.basicConfig(level=bot_configuration.LOGGING_LEVEL)
else:
	logging.basicConfig(filename=bot_configuration.DATA_FOLDER+bot_configuration.LOG_FILE,level=bot_configuration.LOGGING_LEVEL)

#Configure the heartbeat
schedule.every(5).seconds.do(heartbeat.pulse)

#Pulse forever
while True:
	schedule.run_pending()
	time.sleep(1)