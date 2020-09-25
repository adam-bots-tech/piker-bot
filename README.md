# Piker Bot

Stock trading bot for executing swing trades or day trades based off price action while I work. The general idea I had here was to be able to load up a trade journal in my Google Drive with trade setups and then, 
have the bot execute them while I work my software engineering gigs.

This bot DOES NOT attempt to autonmously determine tickers, entry and exit prices on it's own. If it did, it won't be called a piker bot.

This is a very much an alpha work in progress personal project by a software engineer with a bad attitude. It's not for public consumption atm and I don't have a set of solid step by step readme instructions
on how to run it. If you don't have a background in software development, this might be a bit much for you.

## Features
- Reads queued trades from a Google spreadsheet in my Google drive and adds them to it's local sqlite3 database
- Heartbeat pulses every minute and checks the price on tickers from trades in the journal.
- Bot purchases the stock when certain combinations of conditions are met. This is still in testing and tuning.
	- If the bot comes online while the price is above the entry price, it will wait for it to fall below the entry price before
	- flagging the ticker as primed for a trade.
	- Once the price is below the entry price, but above the stop loss, the bot will wait for it to rise above the entry price before proceeding
	- Once the price rises above the entry price, the price must be above the SM5 to show a stable start of an uptrend and the RSI must be under 40(45?) to show it's still oversold.
- Buy orders are good for the day only and then the trade is marked as expired if not filled.
- Bot will sell the stock when combinations of conditions are met. This is still in testing and tuning. At the time of this writing, I think I might be trying to ride an uptrend too hard.
	- First, the price must move within 1% of the entry price.
	- Once the price is within 1% of the entry price, if the RSI goes above 70 at any point, the bot sells immediately. 
	- Or otherwise, the bot waits for the RSI to rise above 60 while the price falls below the SMA3.
- If the trade is flagged with the 'sell at close' boolean, the bot will force a sale within the last 30 minutes of the market being open.
	- It will also prohibit the purchase of shares within the last hour of the market being open. This is to prohibit the bot from immediately opening and closing trades. Might raise this to 1 hour 30 minutes.
- Sale orders are good until canceled to try to keep you from holding bags forever.
- Number Shares to purchase are calculated at the time of the sale, based on how many can be purchased using a percentage of the total brokerage account. 
	- This is based on cash only; not margin buying power. It will not take you into debt to make trades.
- As the trade progreses, the bot automatically updates the sqlite3 database and the trade journal in Google Drive.
	- When it opens or closes a trade, the bot will update the trade journal with a snapshot of technical indicators at the time of purchase or sale. It is also capable of retaining the technical indicators submitted by the trades module in the stock-scripts repo. I plan on writing a script take all of this data and generate html reports for reviewing the trades.
	- It USED TO generate it's own candlestick charts at the time of purchase and sale, but that feature was properly sacked as it caused me a whole bunch of nonsense and weren't very good anyways.

## Libraries
- numpy
- alpaca_trade_api
- ezsheets
- schedule
- beaker
- stockstats

## Configuration and Installation (that may or not work depending on how much coffee I've had)
- Clone the Stock Library repo and follow the README instructions to install locally with pip.
- Clone the piker-bot into the same parent directory containing stock-libaries.
- Copy the example_configuration.py file and rename it bot_configuration.py
- Follow the notes in bot_configuration.py to configure the bot properly.
- The Google Drive API will provide instructions on how to activate the API on a first run.
	- You MUST complete this before you attempt to create the docker image. It will add credentials files that are needed in the docker image.

## Running the Bot

### Docker Image
Run from the parent directory containing the project folder and the stock-libraries module. 
You need to have run it manually once to setup the credentials files for your Google Drive in the piker-bot folder.
Be sure to alter the data folder in bot_configuration.py to point to the mounted folder for the container prior to building.

`docker build -f piker-bot/Dockerfile -t piker-bot .`

`docker run --name piker_bot -d -v [PATH_TO_YOUR_DATA_FOLDER]:/var/lib/piker-bot piker-bot:latest`
Ex: `docker run --name piker_bot -d -v d:/development/docker-data:/var/lib/piker-bot piker-bot:latest`

### Running the Scripts Manually.

You can execute main-pulse.py to fire the heartbeat pulse onxw or run main-scheduler.py to activate
the scheduler and begin pulsing the heartbeat every minute for an eternity. I've used these with windows task scheduler
if you don't know docker, but its not as stable.

How do you set this up in windows tasks scheduler? If you can't google that and figure out, you really shouldn't be messing with this.

## Usage

After the bot runs the first time, a Trade Journal will be created in the root of your Google Drive. It will have a Queued Trades sheet which the bot will pull from when it pulses every minute. It is recommended you fill out your trades
before activating. Once trades are read, they cannot be altered without changing the bot's local sqlite database which means COMMIT to your trades lol.

Columns:
Ticker
Type - long or short. short is not supported right now
Entry Price - float
Exit Price - float
Stop Loss - float
Notes - Text. No '' or "".
Expiration - Number of days to keep the trade queued trade before expiring it. Once a trade is opened, it remains open until sale conditions are met or the 'Sale at End of Day' flag is activated.
Metadata - This is a json data set with technical indicators. It's submitted by the trades module in Stock Scripts. It's a work in progres. It doesn't do anything yet unless you want to read technical indicators out of json data.
Sale at End of Day - If 1, sell at the close of the day the trade is opened. If 0, let the trade ride forever.



