from tasks import now
from bot import format_datetime

spendings = {}



def process_spending(message):
    rmd = message.text.split()
    summ = int(rmd[1])
    category = str(rmd[0]).lower()
    event = ' '.join(rmd[2:])
    if message.from_user.id not in spendings:
        spendings[message.from_user.id] = {}
    if category not in spendings[message.from_user.id]:
        spendings[message.from_user.id][category] = []
    spendings[message.from_user.id][category].append((summ, event, now()))


def display_spending_summary(message):
    sm = sum(amount for cat_spendings in spendings[message.from_user.id].values() for amount, _, _ in cat_spendings)
    formatted_spendings = ', '.join(f"{amount} on {desc} at {format_datetime(spend_date)}" 
                                    for cat_spendings in spendings[message.from_user.id].values() 
                                    for amount, desc, spend_date in cat_spendings)
    tx = f'You spent {sm}. Your spendings: {formatted_spendings}.'
    return tx

def send_report_and_clear_spendings(user_id):
    if user_id in spendings:
        sm = sum(amount for cat_spendings in spendings[user_id].values() for amount, _, _ in cat_spendings)

        formatted_spendings = ', '.join(f"{amount} on {desc} at {format_datetime(spend_date)}" 
                                        for cat_spendings in spendings[user_id].values() 
                                        for amount, desc, spend_date in cat_spendings)

        tx = f'You spent {sm}. Your spendings: {formatted_spendings}.'
        tx = tx.replace('[', '').replace(']', '').replace("'", '')
        txm = 'During this month ' + tx

        bot.send_message(user_id, text=txm, reply_markup=get_keyboard())
        del spendings[user_id]