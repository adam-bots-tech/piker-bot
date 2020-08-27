import bar
import position
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
			return api.get_clock().is_open
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /clock API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	# Return a Position object or None if 404
	def get_position(self, ticker):
		try:
			position = api.get_position(trade.ticker)
			return Position(position.symbol, position.qty, position.avg_entry_price)
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /position API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')

			if err.code == '404':
				return False
			else:
				return None

	# Return a Bar object or None if 404
	def get_last_bar(self, ticker):
		try:
			bar = api.get_barset(trade.ticker, 'minute', 1)[0]
			return Bar(bar)
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /bars/minute API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	# Return order id or None if failed
	def sell(self, trade, sell_price):
		try:
			order = api.submit_order(
			    symbol=trade.ticker,
			    side='sell',
			    type='limit',
			    qty=f'{trade.shares}',
			    time_in_force='day',
			    order_class='simple',
			    limit_price=f'{sell_price}'
			)
			return order.client_order_id
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /order API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	# Return order id or None if failed
	def buy(self, trade, shares, buy_price):
		try:
			order = api.submit_order(
			    symbol=trade.ticker,
			    side='buy',
			    type='limit',
			    qty=f'{shares}',
			    time_in_force='day',
			    order_class='simple',
			    limit_price=f'{buy_price}'
			)
			return order.client_order_id
		except tradeapi.rest.APIError as err:
			logging.error(f'POST /order API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	# Return Order object or None if 404
	def get_order(self, order_id):
		try:
			order = self.api.get_order_by_client_order_id(order_id)
			return Order(order.client_order_id, order.status, order.filled_avg_price, order.qty, order.replaced_by)
		except tradeapi.rest.APIError as err:
			logging.error(f'GET /order API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None

	def get_buying_power(self):
		try:
			account = self.api.get_account()
			return account.buying_power
		except tradeapi.rest.APIError as err:
			logging.error(f'GET /account API Code: {err.code} HTTP Code: {err.statuc_code} Message: {err.message}')
			return None