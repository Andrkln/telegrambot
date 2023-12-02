from tasks import now
from bot import format_datetime
from database import cursor


def process_spending(message):
    rmd = message.text.split()
    summ = int(rmd[1])
    category = str(rmd[0]).lower()
    event = ' '.join(rmd[2:])

    data = [
    (message.from_user.id, category, summ, now(), event),
]

    table_query = """
    INSERT INTO spendings (user_id, category, price, date, event)
    VALUES (%s, %s, %s, %s, %s)
"""

    cursor.executemany(table_query, data)


def display_spending_summary(message):



    user_id = message.from_user.id

    table_query = """
    
    SELECT category, price, date, event FROM spendings
    WHERE user_id = %s
    
    """

    cursor.execute(table_query, (user_id,))

    rows = cursor.fetchall()

    spendings_by_category = {}
    total_spent = 0

    for category, price, date, event in rows:
        total_spent += price
        if category not in spendings_by_category:
            spendings_by_category[category] = []
            spendings_by_category[category].append((price, date, event))

    message_parts = [f"You spent {total_spent}. Your spendings:"]
    for category, spendings in spendings_by_category.items():
        category_total = sum([price for price, _, _ in spendings])
        category_spendings = ', '.join([f"{price} on {event} at {date.strftime('%d.%m %H:%M')}" for price, date, event in spendings])
        message_parts.append(f"{category} {category_total}: {category_spendings}")


    final_message = "\n\n".join(message_parts)


    return final_message


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