# Piker Bot

Stock trading bot for executing planned trades for me while I work

Planned Features:
- Support providing a queue of trades that I can manually add to for the bot to execute when trade slots open.
	- Trade is a ticker, an entry price and an exit price
	- Trades will expire after 5 market days if entry price is not reached.
- Support querying for a view of the status of the trades
- Support canceling a trade in the queue
- Support dynamic leveraging of the account on each trade. 
	- Leverage $100 on each trade until 1% of the account starts to exceed $100, then leverage that
- Scans prices every minute on stocks to...
	- Enter trade when entry price is reached. 
		- Bots sets a starting stop loss based on a risk reward ratio and the delta between entry and exit
	- Set stop loss at the exit price once the exit price is reached.
	- Sell when stop loss is hit or if price exceeds a 2% difference, increase the stop loss until 2% difference is met
	- Repeat until stop loss is finally hit and stock sold.

