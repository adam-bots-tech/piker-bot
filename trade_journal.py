import ezsheets
import bot_configuration

class TradeJournal():

	def bootstrap(self):
		self.journal = self.__get_trade_journal__()

	def __get_trade_journal__(self):
		spreadsheets = ezsheets.listSpreadsheets()

		for key,value in spreadsheets.items():
			if value == bot_configuration.TRADE_JOURNAL_TITLE:
				return ezsheets.Spreadsheet(key)

		return self.__create_trade_journal__();

	def __create_trade_journal__(self):
		ss = ezsheets.createSpreadsheet(bot_configuration.TRADE_JOURNAL_TITLE)
		queued_trades = ss[0]
		queued_trades.title = "Queued Trades"
		queued_trades.updateRow(1, ['Ticker', 'Type', 'Entry Price', 'Exit Price', 'Stop Loss', 'Notes'])
		trades = ss.createSheet('Trades')
		trades.updateRow(1, ['ID', 'Create Date', 'Ticker', 'Type', 'Status', 'Entry Date', 'Exit Date', 'Planned Entry Price', 'Planned Exit Price', 
			'Stop Loss', 'Shares', 'Entry Price', 'Exit Price', 'Buy Order', 'Sell Order', 'Notes', 'Comments'])
		return ss

	def get_queued_trades(self):
		self.journal.refresh()
		return self.journal[0].getRows()

	def reset_queued_trades(self, headerRow):
		self.journal.refresh()
		self.journal[0].updateRows([headerRow])

	def create_queued_trade(self, row_num, ticker, type, entry, exit, stop_loss):
		self.journal.refresh()
		self.journal[0].updateRow(row_num, [ticker, type, entry, exit, stop_loss, ''])


	def create_trade_record(self, trade, notes):
		self.journal.refresh()
		self.journal[1].updateRow(trade.id + 1, [trade.id, trade.create_date, trade.ticker, trade.type, trade.status, trade.entry_date, trade.exit_date, 
			trade.planned_entry_price, trade.planned_exit_price, trade.stop_loss, trade.shares, trade.actual_entry_price, trade.actual_exit_price, trade.buy_order_id, trade.sell_order_id, notes, ''])

	def update_trade_record(self, trade):
		self.journal.refresh()
		row = self.journal[1].getRow(trade.id + 1)
		notes = row[15]
		comments = row[16]
		self.journal[1].updateRow(trade.id + 1, [trade.id, trade.create_date, trade.ticker, trade.type, trade.status, trade.entry_date, trade.exit_date, 
			trade.planned_entry_price, trade.planned_exit_price, trade.stop_loss, trade.shares, trade.actual_entry_price, trade.actual_exit_price, trade.buy_order_id, trade.sell_order_id, notes, comments])
