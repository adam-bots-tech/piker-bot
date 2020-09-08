FROM python:3

RUN apt-get -y update
RUN apt-get install -y cron
RUN apt-get install -u busybox

RUN pip3 install numpy
RUN pip3 install alpaca_trade_api
RUN pip3 install ezsheets

ADD piker-bot/ /app
ADD stock-libraries/ /app-library
RUN pip3 install -e /app-library

ADD piker-bot/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

RUN touch /etc/default/locale
RUN chmod 0644 /etc/default/locale

ADD piker-bot/credentials-sheets.json /root/credentials-sheets.json
ADD piker-bot/token-drive.pickle /root/token-drive.pickle
ADD piker-bot/token-sheets.pickle /root/token-sheets.pickle

WORKDIR /app

CMD busybox syslogd && cron && tail -f /var/log/messages