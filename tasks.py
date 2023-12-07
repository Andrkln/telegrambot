import schedule
import datetime as dt
from bot import bot
from keyboards import get_keyboard
import pytz
import re


jobs_dict = {}

def now():
    timezone = pytz.timezone('Europe/Helsinki')
    return dt.datetime.now(timezone)

def send_task(chat_id, event):
    bot.send_message(chat_id, text=event)

def make_task(message):
    day_regex = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|every day|everyday|working days|weekend)'
    time_regex = r'(\d{1,2}:\d{2})'

    day_match = re.search(day_regex, message.text.lower())
    time_match = re.search(time_regex, message.text)

    if not day_match or not time_match:
        bot.send_message(message.chat.id, text='Invalid format. Please include a day and time.')
        return

    day = day_match.group()
    time = time_match.group()

    schedule_funcs = schedule_dict.get(day)
    if not schedule_funcs:
        bot.send_message(message.chat.id, text='Invalid day. Please specify a valid day.')
        return

    event = re.sub(day_regex, '', message.text)
    event = re.sub(time_regex, '', event).strip()

    if not isinstance(schedule_funcs, list):
        schedule_funcs = [schedule_funcs]

    for schedule_func in schedule_funcs:
        job = schedule_func.at(time).do(send_task, message.chat.id, event)
        jobs_dict[message.from_user.id].append((job, event, day))
    bot.send_message(message.chat.id, text="The task has been added.", reply_markup=get_keyboard())

schedule_dict = {
    'monday': schedule.every().monday,
    'tuesday': schedule.every().tuesday,
    'wednesday': schedule.every().wednesday,
    'thursday': schedule.every().thursday,
    'friday': schedule.every().friday,
    'saturday': schedule.every().saturday,
    'sunday': schedule.every().sunday,
    'every day': schedule.every().day,
    'everyday': schedule.every().day,
    'working days': [schedule.every().monday, schedule.every().tuesday, schedule.every().wednesday, schedule.every().thursday, schedule.every().friday],
    'weekend': [schedule.every().saturday, schedule.every().sunday]
}