FROM python:3

RUN pip3 install numpy
RUN pip3 install alpaca_trade_api
RUN pip3 install ezsheets
RUN pip3 install schedule
RUN pip3 install beaker
RUN pip3 install stockstats

ADD piker-bot/ /app
ADD stock-libraries/ /app-library
RUN pip3 install -e /app-library

ADD piker-bot/credentials-sheets.json /root/credentials-sheets.json
ADD piker-bot/token-drive.pickle /root/token-drive.pickle
ADD piker-bot/token-sheets.pickle /root/token-sheets.pickle

WORKDIR /app

CMD python /app/main-scheduler.py