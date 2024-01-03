import telebot
from telebot import types
from datetime import datetime, timedelta
from weather import get_weather
import schedule
from decouple import config
import threading
import time
import openai
from paint import DallE
from reminder import reminders, set_reminder, reminder_checker
from tasks import jobs_dict, make_task, send_task, now
from bot import bot, format_datetime
from keyboards import R_or_S, get_keyboard
from database import cursor
from spendings import process_spending, display_spending_summary, send_report_and_clear_spendings


user_statuses = {}
scheduled_reports = {}
allowed_users = []



openai.api_key = config("OPENAI_API_KEY")

def parse_datetime(user_input):
    for fmt in ['%d.%m.%Y %H:%M', '%d.%m.%y %H:%M']:
        try:
            return datetime.strptime(user_input, fmt)
        except ValueError:
            pass
    raise ValueError('Invalid date format')
    
@bot.message_handler(commands=['start', 'help',])
def start(message):
    user = message.from_user.username
    if message.from_user.id == int(config('ME')) or user in allowed_users:
        sent_message = bot.send_message(message.chat.id, 
        f'How are you doing {message.from_user.first_name}?', reply_markup=get_keyboard())
    else:
        table_query = """

        SELECT user_name FROM users
        WHERE user_name = %s

        """
        cursor.execute(table_query, (user,))
        rows = cursor.fetchall()
        if str(rows[0][0]) == str(user):
            sent_message = bot.send_message(message.chat.id, 
            f'How are you doing {message.from_user.first_name}?', reply_markup=get_keyboard())
            allowed_users.append(user)
        else:
            bot.send_message(message.chat.id, 'This is a private bot, not for you')



@bot.callback_query_handler(func=lambda c: c.data in [
    'weather', 'spendings', 'remind', 'GPT', 'paint'
    ])
def options(c):
    if c.data == 'weather':
        user_statuses[c.message.chat.id] = 'awaiting_weather_city'
        bot.send_message(c.message.chat.id, text="Give me name of a city")
    elif c.data == 'spendings':
        user_id = c.from_user.id
        table_query = """
        SELECT DISTINCT category FROM spendings
        WHERE user_id = %s
        """
        cursor.execute(table_query, (user_id,))
        user_categories = [row[0] for row in cursor.fetchall()]
        if user_categories:
            markup = types.InlineKeyboardMarkup()
            for category in user_categories:
                button = types.InlineKeyboardButton(text=category, 
                callback_data=f"category_{category}")
                markup.add(button)
            sent_message = bot.send_message(c.message.chat.id, 
            text='Select a category or enter a new one: \n example: cloth 20 shirts for home',  reply_markup=markup)
            user_statuses[c.message.chat.id] = 'awaiting_spendings'
        else:
            bot.send_message(c.message.chat.id, 
            text="write something to to put in spends in format: category price object. \n example: cloth 20 shirts for home")
            user_statuses[c.message.chat.id] = 'awaiting_spendings'
    elif c.data == 'remind':
        bot.send_message(c.message.chat.id, text="What do you want")
        sent_message = bot.send_message(c.message.chat.id, 
        'Do you want to make shedule or reminder', reply_markup=R_or_S())
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
            sent_message = bot.send_message(message.chat.id, 
            text=rweather, 
            reply_markup=get_keyboard())
       
    elif user_status == 'awaiting_spendings':
        try:
            user_id = message.from_user.id
            process_spending(message=message)
            if user_id not in scheduled_reports or not scheduled_reports[user_id]:
                scheduled_reports[user_id] = schedule.every(30).days.at("12:00").do(send_report_and_clear_spendings, message.from_user.id)
            tx = display_spending_summary(message=message)
            del user_statuses[message.chat.id]
            sent_message = bot.send_message(message.chat.id, 
            text=tx, 
            reply_markup=get_keyboard())
       
        except Exception as e:
            tx = f"Error: in spendings {e} Invalid data"
            bot.send_message(message.chat.id, text=tx)
    elif user_status.startswith("selected_"):
        try:
            category = user_status.split("_")[1]
            rmd = message.text.split()
            summ = int(rmd[0])
            event = ' '.join(rmd[1:])

            data = [
            (message.from_user.id, category, summ, now(), event),
                ]

            table_query = """
            INSERT INTO spendings (user_id, category, price, date, event)
            VALUES (%s, %s, %s, %s, %s)
                            """

            cursor.executemany(table_query, data)

            msg = display_spending_summary(message)
            del user_statuses[message.chat.id]
            sent_message = bot.send_message(message.chat.id, 
            text=msg, 
            reply_markup=get_keyboard())
       
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
        sent_message = bot.send_message(message.chat.id, 
        f'{response["choices"][0]["text"]}', parse_mode="None", 
        reply_markup=get_keyboard())
    elif user_status == 'awaiting_paint_description':
        dalle = DallE()
        image = dalle.to_image(message.text)
        del user_statuses[message.chat.id]
        bot.send_message(message.chat.id, text=f'generating')
        sent_message = bot.send_photo(message.chat.id, image, 
        reply_markup=get_keyboard())
    elif user_status == 'make shedule':
        a = message
        make_task(a)
    elif user_status == 'make reminder':
        ab = message
        set_reminder(ab, get_keyboard=get_keyboard())


@bot.callback_query_handler(func=lambda c: c.data in ['Schedule', 'Reminder'])
def schedule_or_reminder_callback(c):
    if c.data == 'Schedule':
        keyboard = show_tasks(c)
        bot.send_message(c.message.chat.id, 
        text="choose day and task in format: monday 10:20 have a breakfast",)
        bot.send_message(c.message.chat.id, 
        text="Available days are: monday, tuesday,  wednesday, thursday, friday, saturday, sunday, every day, working days, weekend",)
        user_statuses[c.message.chat.id] = 'make shedule'
        if c.from_user.id not in jobs_dict:
            jobs_dict[c.from_user.id] = {}
        else:
            sent_message = bot.send_message(c.message.chat.id, 
            'your shedule', reply_markup=keyboard)
       
        sent_message = bot.send_message(c.message.chat.id, 
        'or something else', reply_markup=get_keyboard())
    elif c.data == 'Reminder':
        keyboard = show_reminders(reminders, c.from_user.id)
        user_statuses[c.message.chat.id] = 'make reminder'
        bot.send_message(c.message.chat.id, 
        'Your reminders: tap to delete', 
        reply_markup=keyboard)
        bot.send_message(c.message.chat.id, 
        'Write your reminder in the format: 13.09 10:20 Have breakfast')


@bot.callback_query_handler(func=lambda c: c.data in ['Schedule', 'Reminder'])
def show_tasks(c):
    keyboard = telebot.types.InlineKeyboardMarkup()
    user_id = c.from_user.id
    print(c)
    if c.data == 'Schedule':
        if user_id in jobs_dict:
            for key, job_data in jobs_dict[user_id].items():
                event = job_data[1]
                day = job_data[2]  
                button_text = f"{event}, on {day}"
                callback_data = f"delete_task_{key}"
                button = telebot.types.InlineKeyboardButton(button_text, callback_data=callback_data)
                keyboard.add(button)
    elif c.data == 'Reminder':
        bot.send_message(c.message.chat.id, 'You reminders set.')
        if c.from_user.id in reminders and reminders[c.from_user.id]:
            keyboard = show_reminders(reminders, c.from_user.id)
            bot.send_message(c.message.chat.id, 'Your reminders:', 
            reply_markup=keyboard)
        else:
            bot.send_message(c.message.chat.id, 'You have no reminders set.')
    return keyboard


def show_reminders(reminder_dict, user_id):
    keyboard = types.InlineKeyboardMarkup()
    for index, reminder in enumerate(reminder_dict.get(user_id, [])):
        event = reminder[1]
        reminder_time = reminder[0].strftime('%d.%m %H:%M')
        button_text = f"{event} at {reminder_time}"
        callback_data = f"delete_reminder_{index}"
        button = types.InlineKeyboardButton(button_text, callback_data=callback_data)
        keyboard.add(button)
    return keyboard
       
@bot.callback_query_handler(func=lambda c: 'delete_task_' in c.data)
def delete_task_callback(c):
    job_key = c.data.split('delete_task_')[1]

    if c.from_user.id in jobs_dict and job_key in jobs_dict[c.from_user.id]:
        del jobs_dict[c.from_user.id][job_key]
        response_text = "Task deleted!"
    else:
        response_text = "Task not found or already deleted."

    bot.answer_callback_query(c.id, response_text)
    bot.edit_message_text(chat_id=c.message.chat.id, 
    message_id=c.message.message_id, 
    text="Choose another action or task.")
    msg = bot.send_message(c.message.chat.id, 
    text='Go to start', 
    reply_markup=get_keyboard())
    bot.register_next_step_handler(msg, start)

@bot.callback_query_handler(func=lambda c: 'delete_reminder_' in c.data)
def delete_reminder_callback(c):
    reminder_index = int(c.data.split('_')[-1])
    
    if c.from_user.id in reminders and len(reminders[c.from_user.id]) > reminder_index:
        del reminders[c.from_user.id][reminder_index]
        response_text = "Reminder deleted!"
    else:
        response_text = "Reminder not found."

    bot.answer_callback_query(c.id, response_text)
    bot.edit_message_text(chat_id=c.message.chat.id, 
    message_id=c.message.message_id, 
    text="Choose another action or reminder.")
    msg = bot.send_message(c.message.chat.id, 
    text='Go to start', 
    reply_markup=get_keyboard())
    bot.register_next_step_handler(msg, start)


@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def handle_category_selection(call):
    selected_category = call.data.split("_")[1]
    user_statuses[call.message.chat.id] = f"selected_{selected_category}"
    bot.edit_message_text(chat_id=call.message.chat.id, 
    message_id=call.message.message_id, 
    text=f"Enter amount and description for {selected_category}:")

def run_reminder_checker():
    while True:
        reminder_checker()
        time.sleep(60)

try:
    t3 = threading.Thread(target=bot.infinity_polling, 
    kwargs={'long_polling_timeout': 5, 'timeout': 10})
    t2 = threading.Thread(target=run_reminder_checker)
    t3.start()
    t2.start()
except requests.exceptions.ReadTimeout:
    print("Request timed out. Retrying...")
except Exception as er:
    print(f"Error in end: {er}")
