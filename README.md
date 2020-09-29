# Piker Bot

Stock trading bot for executing swing trades and day trades off price action while I work. The general idea I had here was to be able to load up a trade journal in my Google Drive with trade setups and then, 
have the bot execute the trades for me in a semi-intelligent way while I work on my software engineering gigs.

This bot DOES NOT attempt to autonmously determine tickers, entry and exit prices on it's own. If it did, it won't be called a piker bot.

This is the development repo of the bot and the stability of the code base can be questionable. I will create a tutorial repo when I am done with it.

## Features
- Reads queued trades from a Google spreadsheet in a Google Drive and adds them to a local sqlite3 database.
- Bot's heartbeat pulses every minute and checks the price on tickers from trades in the journal.
- Bot purchases the stock when certain combinations of conditions are met:
	- If the bot comes online while the price is above the entry price, it will wait for it to fall below the entry price before flagging the ticker as primed for a trade. This is to ensure we are taking the trade from a position where the swing is about to begin and prohibiting the bot from buying only to immediately sell when the price rises a few cents later.
	- Once the price is below the entry price, but above the stop loss, the bot will wait for it to rise above the entry price before proceeding to ensure there is some momentum. 
	- Once the price rises above the entry price, the price must be above the SM5 to show the stable start of an uptrend and the RSI must be under 45 to show it's still relatively oversold.
- Buy orders are market price and good for the day only. Trades are marked as expired when the orders are expired. The bot does not attempt to enter them again.
- Bot will sell the stock when combinations of conditions are met:
	- First, the price must move within 1% of the exit price.
	- Once the price is within 1% of the exit price, if the RSI goes above 70 at any point, the bot sells immediately. 
	- Otherwise, if the RSI remains below 70, the bot waits for the price to fall below the SMA3 to show the start of a downtrend before selling.
- If the trade is flagged with the 'sell at close' boolean, the bot will force a sale within the last 30 minutes of the market being open.
	- It will also prohibit the purchase of shares within the last hour of the market being open. This is to prohibit the bot from immediately opening and closing trades.
- Sale orders are market price and good until canceled to try to ensure all trades get closed out at some point
- Number of shares to purchase is calculated at the time of the purchase, based on how many can be purchased using a percentage of the total brokerage account. 
	- This is based on cash only; buying power does not include your margin. It will not take you into debt to make trades.
- As the trade progreses, the bot automatically updates the sqlite3 database and the trade journal in Google Drive.
	- When it opens or closes a trade, the bot will update the trade journal with a snapshot of technical indicators at the time of purchase or sale. 
	- It is also capable of retaining the technical indicators submitted by the trades module in the stock-scripts repo.
	- There is no functionality available making use of this JSON data.

## TO DO
- Add support for short selling

## PIP Libraries
- numpy
- alpaca_trade_api
- ezsheets
- schedule
- beaker
- stockstats
- sqlalchemy

## Configuration and Installation (that may or not work depending on how much coffee I've had)
- Clone the Stock Library repo and follow the README instructions to install locally with pip.
- Clone the piker-bot into the same parent directory containing stock-libaries.
- Copy the example_configuration.py file and rename it bot_configuration.py
- Follow the notes in bot_configuration.py to configure the bot properly.
- Run the following commands on your CMD
	- `pip install numpy`
	- `pip install alpaca_trade_api`
	- `pip install ezsheets`
	- `pip install schedule`
	- `pip install beaker`
	- `pip install stockstats`
	- `pip install sqlalchemy`
- Run the bot once by running the main-pulse.py script.
- The Google Drive API will provide instructions on how to activate the API on a first run.
	- The process will produce three files:
		- credentials-sheets.json
		- token-drive.pickle
		- token-sheets.pickle
	- The process will sometimes create credentials.json instead of credentials-sheets.json. Rename it if so.
	- You MUST complete this step before you attempt to create the docker image. The files are needed inside the container.

## Running the Bot

### Docker Image
Run from the parent directory containing the project folder and the stock-libraries module. 
You need to have run it manually once to setup the credentials files for your Google Drive in the piker-bot folder.
Be sure to alter the data folder in bot_configuration.py to point to the mounted folder for the container prior to building.
	- /var/lib/piker-bot is the mounted virtual folder for the data folder you use for the log and database.

`docker build -f piker-bot/Dockerfile -t piker-bot .`

`docker run --name piker_bot -d -v [PATH_TO_YOUR_DATA_FOLDER]:/var/lib/piker-bot piker-bot:latest`

Ex: `docker run --name piker_bot -d -v d:/development/docker-data:/var/lib/piker-bot piker-bot:latest`

### Running the Scripts Manually.

You can execute main-pulse.py to fire the heartbeat pulse onxw or run main-scheduler.py to activate
the scheduler and begin pulsing the heartbeat every minute for an eternity.

## Usage

After the bot runs the first time, a Trade Journal will be created in the root of your Google Drive. It will have a Queued Trades sheet which the bot will pull from when it pulses every minute. It is recommended you fill out your trades
before activating. Once trades are read, they cannot be altered without changing the bot's local sqlite database which means COMMIT to your trades lol.

Columns:
- Ticker
- Type: long or short. short is not supported right now
- Entry Price: float
- Exit Price: float
- Stop Loss: float
- Notes: Text. No quotes or double quotes or escape characters.
- Expiration: Number of days to keep the trade queued trade before expiring it. Once a trade is opened, it remains open until the sale conditions are met or the 'Sell at End of Day' flag is activated. Must be 1 or greater.
- Metadata: This is a json data set with technical indicators. It's submitted by the trades module in Stock Scripts. It's a work in progres. It doesn't do anything yet unless you want to read technical indicators out of json data. 
- Sell at End of Day: If 1, sell at the close of the day the trade is opened. If 0 or None, let the trade ride forever.



