# Piker Bot

Stock trading bot for executing swing trades over days to weeks. 

## Features
- Reads queued trades from a Google spreadsheet in my Google drive and adds them to local sqlite3 database
- Heartbeat pulses every minute and checks the price on stocks being traded.
- Bot purchases the stock when two conditions are met
	- Price has entered into entry price range.
	- Price moves above SMA3, signaling the start of an uptrend.
- If the price moves into the entry range and falls below the stop loss without shifting into an uptrend, the trade is cancelled.
- Bot will sell the stock when two conditions are met
	- Price moves above the exit price
	- Prices move below SM3, signalling the start of a downtrend
- Shares to purchase is calculated at the time of the sale, based on how many can be purchased using a percentage of the total brokerage account.
- As the trade progreses, the bot automatically updates the sqlite3 database and the trade journal in Google Drive.

## Libraries
Requires a number of libraries available on pip as well as a plotly-orca installation on your PATH.

## Configuration and Installation
- Clone the [Stock Library](https://github.com/adam-long-tech/stock-libraries) repo and follow the README instructions to install locally with pip.
- Clone the piker-bot into the same parent directory containing stock-libaries.
- Copy the example_configuration.py file and rename it bot_configuration.py
- Follow the notes in bot_configuration.py to configure the bot properly.
- The Google Drive API will provide instructions on how to activate the API on a first run.

## Running the Bot

I had a docker image, but it was too difficult to get the logging to work with crontab, so it has been sidelined for the time being.

You can execute main-pulse.py to fire the heartbeat pulse onxw or run main-scheduler.py to activate
the scheduler and begin pulsing the heartbeat every minute for an eternity.

