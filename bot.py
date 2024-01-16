from decouple import config
import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import datetime as dt
import pytz

timezone = pytz.timezone('Europe/Helsinki')

bot = telebot.TeleBot(config('BOT_TOKEN'))

scheduler = BackgroundScheduler(timezone=timezone)
scheduler.start()


def format_datetime(dt):
    return dt.strftime('%d.%m %H:%M')