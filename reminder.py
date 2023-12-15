import datetime as dt
from tasks import send_task, now
from bot import bot
from keyboards import get_keyboard
import pytz

reminders = {}

def set_reminder(message, get_keyboard):
    try:
        rmd = message.text.split(" ")
        date_part = rmd[0]
        time_part = rmd[1]
        event = ' '.join(rmd[2:])
        combined_date_time = f"{date_part} {time_part}"

        for fmt in ['%d.%m %H:%M', '%d.%m %H:%M', '%d.%m %H:%M', '%d.%m %H:%M']:
            try:
                tdate = dt.datetime.strptime(combined_date_time, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError("Invalid date format")

        timezone = pytz.timezone('Europe/Helsinki')
        tdate = timezone.localize(tdate.replace(year=now().year))
        
    except Exception as e:
        bot.send_message(message.chat.id, text=f"Invalid data: {e}")
        return

    if tdate < dt.datetime.now(timezone):
            bot.send_message(message.chat.id, 
            text="Cannot set a reminder for a past time.", 
            reply_markup=get_keyboard())
            return

    if message.from_user.id in reminders.keys():
        reminders[message.from_user.id].append((tdate, event))
    else:
        reminders[message.from_user.id] = [(tdate, event)]
    
    tx = 'Reminder set successfully!'
    bot.send_message(message.chat.id, text=tx, reply_markup=get_keyboard)



def reminder_checker():
    timezone = pytz.timezone('Europe/Helsinki')
    now = dt.datetime.now(timezone)
    to_remove = []
    for user_id, user_reminders in reminders.items():
        for reminder in user_reminders:
            if now > reminder[0]:
                send_task(user_id, f"Reminder: {reminder[1]}")
                to_remove.append((user_id, reminder))

    for user_id, reminder in to_remove:
        reminders[user_id].remove(reminder)

