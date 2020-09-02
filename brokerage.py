import bar
import position
import order
import bot_configuration
import alpaca_trade_api as tradeapi

class Brokerage:

	def __init__(self):
		if (bot_configuration.ALPACA_PAPER_TRADING_ON == True):
			self.api = tradeapi.REST(bot_configuration.ALPACA_KEY_ID, bot_configuration.ALPACA_SECRET_KEY, base_url='https://paper-api.alpaca.markets')
		else:
			self.api = tradeapi.REST(bot_configuration.ALPACA_KEY_ID, bot_configuration.ALPACA_SECRET_KEY)

	def is_open(self):
		try:
			return self.api.get_clock().is_open
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /clock API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	# Return a Position object or None if 404
	def get_position(self, ticker):
		try:
			p = self.api.get_position(ticker)
			return position.Position(p.symbol, p.qty, p.avg_entry_price)
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /position API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')

			if err.code == '404':
				return False
			else:
				return None

	# Return a Bar object or None if 404
	def get_last_bar(self, ticker):
		try:
			barset = self.api.get_barset(ticker, 'minute', 1)
			return bar.Bar(barset[ticker][0])
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /bars/minute API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	# Return order id or None if failed
	def sell(self, ticker, shares):
		try:
			order = self.api.submit_order(
			    symbol=ticker,
			    side='sell',
			    type='market',
			    qty=f'{shares}',
			    time_in_force='gtc',
			    order_class='simple'
			)
			return order.client_order_id
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /order API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	# Return order id or None if failed
	def buy(self, ticker, shares):
		try:
			order = self.api.submit_order(
			    symbol=ticker,
			    side='buy',
			    type='market',
			    qty=f'{shares}',
			    time_in_force='day',
			    order_class='simple'
			)
			return order.client_order_id
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /order API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	# Return Order object or None if 404
	def get_order(self, order_id):
		try:
			o = self.api.get_order_by_client_order_id(order_id)
			return order.Order(o.client_order_id, o.status, o.filled_avg_price, o.qty, o.replaced_by)
		except tradeapi.rest.APIError as err:
			logging.error(f'GET /order API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	def get_buying_power(self):
		try:
			account = self.api.get_account()
			return float(account.cash)
		except tradeapi.rest.APIError as err:
			logging.error(f'GET /account API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None