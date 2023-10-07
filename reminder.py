import datetime as dt
from tasks import send_task, now
from bot import bot
from keyboards import get_keyboard

reminders = {}


def set_reminder(message, get_keyboard):
            try:
                rmd = message.text.split(" ")
                date_part = rmd[0]
                time_part = rmd[1]
                event = ' '.join(rmd[2:])
                combined_date_time = f"{date_part} {time_part}"
                tdate = dt.datetime.strptime(combined_date_time, '%d.%m %H:%M')
            except:
                bot.send_message(message.chat.id, text="Invalid data")
            tdate = tdate.replace(year=now().year)
            delta_time = (tdate - now()).total_seconds()
            if delta_time < 0:
                bot.send_message(message.chat.id, text="The specified time is in the past. Please set a future time.")
                return

            if message.from_user.id in reminders.keys():
                reminders[message.from_user.id].append((tdate, event))
            else:
                reminders[message.from_user.id] = [(tdate, event)]
            
            tx = 'Reminder set successfully!'
            bot.send_message(message.chat.id, text=tx, reply_markup=get_keyboard())


def reminder_checker():
    now = dt.datetime.now()
    to_remove = []
    for user_id, user_reminders in reminders.items():
        for reminder in user_reminders:
            if now > reminder[0]:
                send_task(bot, user_id, f"Reminder: {reminder[1]}")
                to_remove.append((user_id, reminder))

    for user_id, reminder in to_remove:
        reminders[user_id].remove(reminder)

