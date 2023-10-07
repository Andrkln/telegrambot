from decouple import config
import telebot
bot = telebot.TeleBot(config('BOT_TOKEN'))