import telebot
from telebot import types
import datetime as dt
from datetime import datetime
from weather import get_weather
import schedule
from decouple import config
import threading
import time
import openai
from paint import DallE
from reminder import reminders, set_reminder, reminder_checker
from tasks import jobs_dict, make_task, send_task, now
from bot import bot
from keyboards import R_or_S, get_keyboard

spendings = {}
user_statuses = {}
scheduled_reports = {}



openai.api_key = config("OPENAI_API_KEY")

def format_datetime(dt):
    return dt.strftime('%d.%m %H:%M')

def parse_datetime(user_input):
    for fmt in ['%d.%m.%Y %H:%M', '%d.%m.%y %H:%M']:
        try:
            return datetime.strptime(user_input, fmt)
        except ValueError:
            pass
    raise ValueError('Invalid date format')
    
@bot.message_handler(commands=['start', 'help',])
def start(message):
    if message.from_user.id == int(config('ME')):
        bot.send_message(message.chat.id, f'How are you doing {message.from_user.first_name}?',reply_markup=get_keyboard())
    else:
        bot.send_message(message.chat.id, 'this is a private bot, not for you')


@bot.callback_query_handler(func=lambda c: c.data in ['weather', 'spendings', 'remind', 'GPT', 'paint'])
def options(c):
    if c.data == 'weather':
        user_statuses[c.message.chat.id] = 'awaiting_weather_city'
        bot.send_message(c.message.chat.id, text="Give me name of a city")
    elif c.data == 'spendings':
        bot.send_message(c.message.chat.id, text="Напишите что-нибудь, если хотите создать или попонить список расходов в вормате: 8000 футболка гучи")
        user_statuses[c.message.chat.id] = 'awaiting_spendings'
    elif c.data == 'remind':
        bot.send_message(c.message.chat.id, text="What do you want")
        bot.send_message(c.message.chat.id, 'Do you want to make shedule or reminder', reply_markup=R_or_S())
    elif c.data == 'GPT':
        bot.send_message(c.message.chat.id, text="Type your question")
        user_statuses[c.message.chat.id] = 'awaiting_gpt_question'
    elif c.data == 'paint':
        bot.send_message(c.message.chat.id, text="Type your image description")
        user_statuses[c.message.chat.id] = 'awaiting_paint_description'


@bot.message_handler(func=lambda message: True)
def handle_user_message(message):
    user_status = user_statuses.get(message.chat.id)
    if user_status == 'awaiting_weather_city':
        rmd = message.text
        city = get_weather(rmd)
        if city == False:
            bot.send_message(message.chat.id, text=f'Sorry wrong name')
        else:
            temp = city['main']['temp']
            feels_like = city['main']['feels_like']
            cweather = city['weather'][0]['main']
            rweather = f'weaher in city {rmd}: {cweather} temperature {temp}, feels like {feels_like}'
            del user_statuses[message.chat.id]
            bot.send_message(message.chat.id, text=rweather, reply_markup=get_keyboard())
    elif user_status == 'awaiting_spendings':
        try:
            rmd = message.text
            rmd = rmd.split(" ")
            summ = int(rmd[0])
            event = ' '.join(rmd[1::])
            if message.from_user.id in spendings.keys():
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
                del user_statuses[message.chat.id]
                bot.send_message(message.chat.id, text=tx, reply_markup=get_keyboard())
            else:
                spendings[message.from_user.id] = [(summ, event, now())]
                del user_statuses[message.chat.id]
                tx = 'You did not spend any money before, that is your first note'
                if user_id not in scheduled_reports or not scheduled_reports[user_id]:
                    scheduled_reports[user_id] = schedule.every(30).days.at("12:00").do(send_report_and_clear_spendings, message.from_user.id)
                bot.send_message(message.chat.id, text=tx, reply_markup=get_keyboard())
        except:
            tx = 'Invalid data'
            bot.send_message(message.chat.id, text=tx)
    elif user_status == 'awaiting_gpt_question':
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f'"""\n{message.text}\n"""',
            temperature=0,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=['"""'],
        )
        del user_statuses[message.chat.id]
        bot.send_message(message.chat.id, f'{response["choices"][0]["text"]}', parse_mode="None", reply_markup=get_keyboard())
    elif user_status == 'awaiting_paint_description':
        dalle = DallE()
        image = dalle.to_image(message.text)
        del user_statuses[message.chat.id]
        bot.send_message(message.chat.id, text=f'generating')
        bot.send_photo(message.chat.id, image, reply_markup=get_keyboard())
    elif user_status == 'make shedule':
        a = message
        make_task(a)
    elif user_status == 'make reminder':
        ab = message
        set_reminder(ab, get_keyboard=get_keyboard)

def send_report_and_clear_spendings(user_id):
    if user_id in spendings:
        sm = sum(i[0] for i in spendings[user_id])
        formatted_spendings = [(amount, desc, format_datetime(spend_date)) for amount, desc, spend_date in spendings[user_id]]
        tx = f'you spent {sm}, your spendings: {formatted_spendings}'
        tx = tx.replace('[', '')
        tx = tx.replace(']', '')
        tx = tx.replace("'", '')
        txm = 'During this month ' + tx
        bot.send_message(user_id, text=txm, reply_markup=get_keyboard())
        del spendings[user_id]



@bot.callback_query_handler(func=lambda c: c.data in ['Schedule', 'Reminder'])
def schedule_or_reminder_callback(c):
    if c.data == 'Schedule':
        bot.send_message(c.message.chat.id, text="choose day and task in format: monday 10:20 have a breakfast",)
        bot.send_message(c.message.chat.id, text="Available days are: monday, tuesday,  wednesday, thursday, friday, saturday, sunday, every_day, working_days, weekend",)
        user_statuses[c.message.chat.id] = 'make shedule'
        if c.from_user.id not in jobs_dict:
            jobs_dict[c.from_user.id] = []
        else:
            bot.send_message(c.message.chat.id, 'your shedule', reply_markup=show_tasks(jobs_dict, c.from_user.id))
        bot.send_message(c.message.chat.id, 'or something else', reply_markup=get_keyboard())
    elif c.data == 'Reminder':
        user_statuses[c.message.chat.id] = 'make reminder'
        bot.send_message(c.message.chat.id, 'Write your reminder in the format: 13.09 10:20 Have breakfast')
       
@bot.callback_query_handler(func=lambda c: 'delete_task_' in c.data)
def delete_task_callback(c):
    job_index = int(c.data.split('_')[-1])
    del jobs_dict[c.from_user.id][job_index]
    bot.answer_callback_query(c.id, "Task deleted!")
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text="Choose another action or task.",)
    msg = bot.send_message(c.message.chat.id, text='go to start', reply_markup=get_keyboard())
    bot.register_next_step_handler(msg, start)

@bot.callback_query_handler(func=lambda c: 'delete_reminder_' in c.data)
def delete_reminder_callback(c):
    reminder_index = int(c.data.split('_')[-1])
    del reminders[c.from_user.id][reminder_index]
    bot.answer_callback_query(c.id, "Reminder deleted!")
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text="Choose another action or reminder.",)
    msg = bot.send_message(c.message.chat.id, text='go to start', reply_markup=get_keyboard())
    bot.register_next_step_handler(msg, start)

@bot.callback_query_handler(func=lambda c: c.data in [' delete Schedule', ' delete Reminder'])
def show_tasks(task, id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for index, job_data in enumerate(task[id]):
        event = job_data[1]
        day = job_data[2]
        button_text = f"{event}, ||| {day}"
        callback_data = f"delete_task_{index}"
        button = telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data)
        keyboard.add(button)
    return keyboard


def show_reminders(reminder_dict, user_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    for index, reminder_data in enumerate(reminder_dict[user_id]):
        event = reminder_data[1]
        date_time = reminder_data[0].strftime('%d.%m %H:%M')
        button_text = f"{event}, ||| {date_time}"
        callback_data = f"delete_reminder_{index}"
        button = telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data)
        keyboard.add(button)

    button2 = telebot.types.InlineKeyboardButton('weather', callback_data='weather')
    button3 = telebot.types.InlineKeyboardButton('spendings', callback_data='spendings')
    button4 = telebot.types.InlineKeyboardButton('remind', callback_data='remind')
    keyboard.add(button2, button3, button4)
    return keyboard

def run_reminder_checker():
    while True:
        reminder_checker()
        time.sleep(60)


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

try:
    t = threading.Thread(target=run_schedule)
    t2 = threading.Thread(target=run_reminder_checker)
    t.start()
    t2.start()
    reminder_checker()
    bot.polling(none_stop=True, interval=0, timeout=20)
except Exception as e:
    time.sleep(5)
    print(f"Error: {e}")