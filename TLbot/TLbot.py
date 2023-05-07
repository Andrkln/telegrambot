import telebot
from telebot import types
import datetime as dt
from datetime import datetime
from weather import get_weather
import schedule


reminders = {}
spendings = {}
shedulte_dict = {}

bot = telebot.TeleBot("5180025628:AAHb1YPzLqGWuPyYCFpTCoRIpnefDz43wGo")


def format_datetime(dt):
    return dt.strftime('%d.%m.%y %H:%M')

def parse_datetime(user_input):
    for fmt in ['%d.%m.%Y %H:%M', '%d.%m.%y %H:%M']:
        try:
            return datetime.strptime(user_input, fmt)
        except ValueError:
            pass
    raise ValueError('Invalid date format')

def now():
    now = dt.datetime.now()
    current_time = now.strftime("%d.%m.%Y %H:%M")
    current_time = dt.datetime.strptime(current_time, '%d.%m.%Y %H:%M')
    return current_time


bot = telebot.TeleBot("5180025628:AAHb1YPzLqGWuPyYCFpTCoRIpnefDz43wGo")
@bot.message_handler(commands=['start', 'help',])
def start(message):
    bot.send_message(message.chat.id, f'How are you doing {message.from_user.first_name}?',reply_markup=get_keyboard())
    bot.send_message(message.chat.id, f'My additional functions {message.from_user.first_name}?',reply_markup=other_bots())
    if message.text == "ChatGPT":
        bot.send_message(message.chat.id, f'What you wanna know {message.from_user.first_name} ?')
        msg = bot.reply_to(message, 'Вот опциий')
        bot.register_next_step_handler(msg,ChatGPT)
    if message.text == "Drawings":
        bot.send_message(message.chat.id, f'What you wanna know {message.from_user.first_name} ?')
        msg = bot.reply_to(message, 'Вот опциий')
        bot.register_next_step_handler(msg,Drawings)

def ChatGPT(message):
    pass
def Drawings(message):
    pass


@bot.callback_query_handler(func=lambda c: c.data in ['weather', 'spendings', 'remind'])
def options(c):
    if c.data == 'weather':
        bot.send_message(c.message.chat.id, text="Give me name of a city")
        @bot.message_handler()
        def swether(message):
            rmd = message.text
            city = get_weather(rmd)
            if city == False:
                bot.send_message(c.message.chat.id, text=f'Sorry wrong name')
            else:
                temp = city['main']['temp']
                feels_like = city['main']['feels_like']
                cweather = city['weather'][0]['main']
                rweather = f'weaher in city {rmd}: {cweather} temperature {temp}, feels like {feels_like}'
                bot.send_message(c.message.chat.id, text=rweather)
    elif c.data == 'spendings':
        bot.send_message(c.message.chat.id, text="Напишите что-нибудь, если хотите создать или попонить список расходов в вормате: 8000 футболка гучи")
        @bot.message_handler()
        def spends(message):
            rmd = message.text
            rmd = rmd.split(" ")
            summ = int(rmd[0])
            event = ' '.join(rmd[1::])
            if message.from_user.id in spendings.keys():
                print(spendings)
                p = spendings[message.from_user.id]
                p.append((summ, event, now()))
                sm = 0
                for i in spendings[message.from_user.id]:
                    sm += i[0]
                formatted_spendings = [(amount, desc, format_datetime(spend_date)) for amount, desc, spend_date in spendings[message.from_user.id]]
                tx = f'you spent {sm}, your spendings: {formatted_spendings}'
                tx = tx.replace('[', '')
                tx = tx.replace(']', '')
                tx = tx.replace("'", '')
                bot.send_message(c.message.chat.id, text=tx)
            else:
                spends = []
                spends = spends.append((summ, event))
                spendings[message.from_user.id] = spends
                bot.send_message(c.message.chat.id, text='You did not spend any money')
    elif c.data == 'remind':
        bot.send_message(c.message.chat.id, text="What do you want")
        bot.send_message(c.message.chat.id, 'Do you want to make shedule or reminder', reply_markup=R_or_S())

             

@bot.callback_query_handler(func=lambda c: c.data in ['Schedule', 'Reminder'])
def schedule_or_reminder_callback(c):
    if c.data == 'Schedule':
        bot.send_message(c.message.chat.id, text="choose what days of a week you want to do something ?", reply_markup=week())
    elif c.data == 'Reminder':
        @bot.message_handler()
        def spends(message):
            rmd = message.text
            rmd = rmd.split(" ")
            event = ' '.join(rmd[2::])
            dates = ' '.join(rmd[0:2])
            tdate = tdate = parse_datetime(dates)
            if message.from_user.id in reminders.keys():
                p = reminders[message.from_user.id]
                p.append((tdate, event))
                tx = f'You have {len(reminders[message.from_user.id])} notes, your notes: {[f"{format_datetime(dt)} {event}" for dt, event in reminders[message.from_user.id]]}'
                tx = tx.replace('[', '')
                tx = tx.replace(']', '')
                tx = tx.replace("'", '')
                bot.send_message(c.message.chat.id, text=tx)
            else:
                reminds = []
                reminds.append((tdate, event))
                reminders[message.from_user.id] = reminds
                bot.send_message(c.message.chat.id, text="You've created your first note ")


@bot.callback_query_handler(func=lambda c: c.data in ['monday', 'tuesday','wednesday','trusday','friday','saturday', 'sunday', 'every_day', 'weekend', 'working_days'])
def spends(c):
    if c.data == 'monday':
        bot.send_message(c.message.chat.id, text='choose time and task in format: 10:20 have a breakfast')
        @bot.message_handler()
        def make_manday_task(message):
            rmd = message.text
            shedulte_dict[message.from_user.id] = rmd
            rmd = rmd.split(" ")
            time = rmd[0]
            event = ' '.join(rmd[1::])
            schedule.every().monday.at(time).do()
    if c.data == 'tuesday':
        pass
    if c.data == 'wednesday':
        pass
    if c.data == 'trusday':
        pass
    if c.data == 'friday':
        pass
    if c.data == 'saturday':
        pass
    if c.data == 'sunday':
        pass
    if c.data == 'every_day':
        pass
    if c.data == 'weekend':
        pass
    if c.data == 'working_days':
        pass

def get_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton('Weather in a city', callback_data='weather')
    button2 = telebot.types.InlineKeyboardButton('Spendings', callback_data='spendings')
    button3 = telebot.types.InlineKeyboardButton('Remiders and Schedule', callback_data='remind')
    keyboard.add(button, button2, button3)
    return keyboard

def other_bots():
    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
    item1 = types.KeyboardButton("ChatGPT")
    item2 = types.KeyboardButton("Drawings")
    markup.add(item1, item2)
    return markup

def R_or_S():
    keyboard = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton('Make a schedule', callback_data='Schedule')
    button2 = telebot.types.InlineKeyboardButton('Make a reminder', callback_data='Reminder')
    keyboard.add(button1, button2)
    return keyboard

def week():
    keyboard = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton('monday', callback_data='monday')
    button2 = telebot.types.InlineKeyboardButton('tuesday', callback_data='tuesday')
    button3 = telebot.types.InlineKeyboardButton('wednesday', callback_data='wednesday')
    button4 = telebot.types.InlineKeyboardButton('trusday', callback_data='trusday')
    button5 = telebot.types.InlineKeyboardButton('friday', callback_data='friday')
    button6 = telebot.types.InlineKeyboardButton('saturday', callback_data='saturday')
    button7 = telebot.types.InlineKeyboardButton('sunday', callback_data='sunday')
    button8 = telebot.types.InlineKeyboardButton('everyday', callback_data='every_day')
    button9 = telebot.types.InlineKeyboardButton('weekend', callback_data='weekend')
    button10 = telebot.types.InlineKeyboardButton('working days', callback_data='working_days')
    keyboard.add(button1, button2, button3, button4, button5, button6, button7, button8, button9, button10)
    return keyboard

bot.infinity_polling()