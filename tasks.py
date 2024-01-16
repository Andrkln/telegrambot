import schedule
import datetime as dt
from bot import bot
from keyboards import get_keyboard
import re
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from bot import scheduler
import pytz

jobs_dict = {}


def now():
    timezone = pytz.timezone('Europe/Helsinki')
    return dt.datetime.now(timezone)

def send_task(chat_id, event):
    bot.send_message(chat_id, text=event)

def make_task(message):
    day_regex = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|every_day|everyday|working_days|weekend)'
    time_regex = r'(\d{1,2}):(\d{2})'

    user_id = message.from_user.id
    user_jobs = jobs_dict.get(user_id, {})

    day_match = re.search(day_regex, message.text.lower().replace(' ', '_'))
    time_match = re.search(time_regex, message.text)

    if not day_match or not time_match:
        bot.send_message(message.chat.id, 
        text='Invalid format. Please include a day and time.')
        return

    day = day_match.group()
    hour, minute = time_match.groups()

    event = re.sub(day_regex, '', str(message.text).lower())
    event = re.sub(time_regex, '', event).strip()

    days = {
        'monday': 'mon',
        'tuesday': 'tue',
        'wednesday': 'wed',
        'thursday': 'thu',
        'friday': 'fri',
        'saturday': 'sat',
        'sunday': 'sun',
        'every_day': '*',
        'everyday': '*',
        'working_days': 'mon-fri',
        'weekend': 'sat,sun'
    }
    
    cron_day = days.get(day, '*')

    now_in_timezone = now()

    job_key = f"{message.from_user.id}_{now_in_timezone.strftime('%Y%m%d%H%M%S')}"

    job = scheduler.add_job(send_task, 
    trigger=CronTrigger(day_of_week=cron_day, 
    hour=hour, minute=minute),
    timezone=now(), 
    args=[message.chat.id, event])
    
    user_jobs[job_key] = (job, event, day)
    jobs_dict[user_id] = user_jobs

    bot.send_message(message.chat.id, 
    text="The task has been added.", 
    reply_markup=get_keyboard())