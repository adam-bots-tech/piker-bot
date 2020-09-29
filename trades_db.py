from datetime import datetime
import logging
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bot_configuration
import json

Base = declarative_base()

class Trade(Base):
	__tablename__ = 'trades'
	id=Column(Integer, primary_key=True, autoincrement=True)
	shares = Column(Float)
	planned_exit_price = Column(Float)
	planned_entry_price = Column(Float)
	create_date = Column(Float)
	entry_date = Column(Float)
	exit_date = Column(Float)
	stop_loss = Column(Float)
	actual_exit_price = Column(Float)
	actual_entry_price = Column(Float)
	status=Column(Text)
	ticker=Column(Text)
	sell_order_id=Column(Text)
	buy_order_id=Column(Text)
	type=Column(Text)
	expiration_date=Column(Integer)
	sell_at_end_day=Column(Integer)

class Property(Base):
	__tablename__ = 'state'
	key = Column(Text, primary_key=True)
	value = Column(Text)

Engine = create_engine('sqlite:///'+bot_configuration.DATA_FOLDER+bot_configuration.DATABASE_NAME)
Base.metadata.create_all(Engine)
Base.metadata.bind = Engine
DBSession = sessionmaker(bind=Engine)
Session = DBSession()

def generate_default_trade(ticker, type, entry, exit, stop_loss, expiration_date, sell_at_end_day):
	trade = Trade()
	trade.create_date = datetime.timestamp(datetime.now())
	trade.ticker = ticker
	trade.type=type
	trade.planned_entry_price=entry
	trade.planned_exit_price=exit
	trade.status="QUEUED"
	trade.expiration_date=expiration_date
	trade.sell_at_end_day=sell_at_end_day
	trade.shares = 0.0
	trade.actual_entry_price=0.0
	trade.actual_exit_price=0.0
	trade.stop_loss=stop_loss
	trade.exit_date=0.0
	trade.entry_date=0.0
	trade.buy_order_id=''
	trade.sell_order_id=''
	return trade

def get(create_date):
	return Session.query(Trade).filter(Trade.create_date == create_date).one()

def get_by_ticker(ticker):
	return Session.query(Trade).filter(Trade.ticker == ticker).first()

def add(trade):
	Session.add(trade)
	Session.commit()
	return get(trade.create_date)

def create_new_long_trade(ticker, entry, exit, stop_loss, expiration_date, sell_at_end_day):
	return add(generate_default_trade(ticker, 'long', entry, exit, stop_loss, expiration_date, sell_at_end_day))

def open(trade, shares, price):
	trade.shares = shares
	trade.status = 'OPEN'
	trade.actual_entry_price = price
	trade.entry_date = datetime.timestamp(datetime.now())
	Session.commit()
	remove_buy_price_marker(trade.ticker, trade.id)
	return trade

def close(trade, price):
	trade.status = 'CLOSED'
	trade.actual_exit_price = price
	trade.exit_date = datetime.timestamp(datetime.now())
	Session.commit()
	remove_sale_price_marker(trade.ticker, trade.id)
	return trade

def cancel(trade):
	trade.status = 'CANCELED'
	Session.commit()
	remove_buy_price_marker(trade.ticker, trade.id)
	remove_buy_price_marker(trade.ticker, trade.id)
	return trade

def cancel_sale(trade):
	trade.status = 'SALE_CANCELED'
	Session.commit()
	remove_sale_price_marker(trade.ticker, trade.id)
	return trade

def invalidate(trade):
	trade.status = 'MISSING'
	Session.commit()
	return trade

def out_of_money(trade):
	trade.status = 'FUNDS_TOO_LOW'
	Session.commit()
	return trade

def sell(trade, order_id):
	trade.status = 'SELLING'
	trade.sell_order_id = order_id
	Session.commit()
	remove_sale_price_marker(trade.ticker, trade.id)
	return trade

def buy(trade, shares, order_id):
	trade.status = 'BUYING'
	trade.shares = shares
	trade.buy_order_id = order_id
	Session.commit()
	remove_buy_price_marker(trade.ticker, trade.id)
	return trade

def replace_sale(trade, order_id):
	trade.status = 'SELLING'
	trade.sell_order_id = order_id
	Session.commit()
	remove_sale_price_marker(trade.ticker, trade.id)
	return trade

def replace_buy(trade, order_id):
	trade.status = 'BUYING'
	trade.buy_order_id = order_id
	Session.commit()
	remove_buy_price_marker(trade.ticker, trade.id)
	return trade

def expire(trade):
	trade.status = 'EXPIRED'
	Session.commit()
	remove_buy_price_marker(trade.ticker, trade.id)
	return trade

def expire_sale(trade):
	trade.status = 'SALE_EXPIRED'
	Session.commit()
	remove_sale_price_marker(trade.ticker, trade.id)
	return trade

def update_stop_loss(trade, stop_loss):
	trade.stop_loss = stop_loss
	Session.commit()
	return trade


def get_all_trades():
	return Session.query(Trade).order_by(Trade.create_date.asc()).all()

def get_open_long_trades():
	return Session.query(Trade).filter(Trade.status == 'OPEN', Trade.type == 'long').order_by(Trade.create_date.asc()).all()

def get_trades_being_bought():
	return Session.query(Trade).filter(Trade.status == 'BUYING').order_by(Trade.create_date.asc()).all()

def get_trades_being_sold():
	return Session.query(Trade).filter(Trade.status == 'SELLING').order_by(Trade.create_date.asc()).all()

def get_active_trades():
	return Session.query(Trade).filter(Trade.status.in_(['OPEN', 'BUYING', 'SELLING'])).order_by(Trade.create_date.asc()).all()

def get_queued_trades():
	return Session.query(Trade).filter(Trade.status == 'QUEUED').order_by(Trade.create_date.asc()).all()


def get_queued_long_trades():
	return Session.query(Trade).filter(Trade.status == 'QUEUED', Trade.type == 'long').order_by(Trade.create_date.asc()).all()

cache = {
	'market_open': None,
	'prices': None
}

def get_market_open():
	if cache['market_open'] is None:
		cache['market_open'] = Session.query(Property).filter(Property.key == 'market_open').first()
	return cache['market_open'] is not None and cache['market_open'] == 'True'

def get_last_prices():
	if cache['prices'] is None:
		cache['prices'] = Session.query(Property).filter(Property.key == 'last_prices').first()
	return {} if cache['prices'] is None or cache['prices'].value is None else json.loads(cache['prices'].value)

def set_market_open(is_open):
	if cache['market_open'] is None:
		cache['market_open'] = Property(key='market_open', value=is_open)
		Session.add(cache['market_open'])
		Session.commit()
	else:
		cache['market_open'].value = is_open
		Session.commit()

def set_last_prices(last_prices):
	if cache['prices'] is None:
		cache['prices'] = Property(key='last_prices', value=json.dumps(last_prices))
		Session.add(cache['prices'])
		Session.commit()
	else:
		cache['prices'].value=json.dumps(last_prices)
		Session.commit()

def remove_buy_price_marker(ticker, id):
	prices = get_last_prices()
	if 'buy'+ticker+str(id) in prices.keys():
		del prices['buy'+ticker+str(id)]
	set_last_prices(prices)

def remove_sale_price_marker(ticker, id):
	prices = get_last_prices()
	if 'buy'+ticker+str(id) in prices.keys():
		del prices['buy'+ticker+str(id)]
	set_last_prices(prices)

def set_sale_price_marker(ticker, id):
	prices = get_last_prices()
	prices['sell'+ticker+str(id)] = True
	set_last_prices(prices)

def get_sale_price_marker(ticker, id):
	prices = get_last_prices()
	if 'sell'+ticker+str(id) not in prices.keys() or prices['sell'+ticker+str(id)] == False: 
		return False
	else:
		return True

def set_buy_price_marker(ticker, id):
	prices = get_last_prices()
	prices['buy'+ticker+str(id)] = True
	set_last_prices(prices)

def get_buy_price_marker(ticker, id):
	prices = get_last_prices()
	if 'buy'+ticker+str(id) not in prices.keys() or prices['buy'+ticker+str(id)] == False: 
		return False
	else:
		return True