from decouple import config
import telebot
bot = telebot.TeleBot(config('BOT_TOKEN'))

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

import datetime as dt

def format_datetime(dt):
    return dt.strftime('%d.%m %H:%M')