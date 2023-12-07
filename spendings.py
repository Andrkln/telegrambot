from tasks import now
from bot import format_datetime
from database import cursor
from tasks import now
from bot import bot


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
        category_spendings = ', '.join([f"{price} on {event} at {date.strftime('%d.%m %H:%M')}\n" for price, date, event in spendings])
        message_parts.append(f"{category} {category_total}: {category_spendings}")



    final_message = "\n\n".join(message_parts)


    return final_message


def send_report_and_clear_spendings(user_id):
    year = now().year
    month = now().month - 1 if now().month > 1 else 12
    year = year if now().month > 1 else year - 1

    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month+1:02d}-01" if month < 12 else f"{year+1}-01-01"

    table_query = """
        SELECT category, price, date, event 
        FROM spendings
        WHERE user_id = %s AND date >= %s AND date < %s
    """

    cursor.execute(table_query, (user_id, start_date, end_date))
    rows = cursor.fetchall()

    if not rows:
        bot.send_message(user_id, text="No spendings recorded for this month.")
        return

    spendings_by_category = {}
    total_spent = 0

    for category, price, date, event in rows:
        total_spent += price
        if category not in spendings_by_category:
            spendings_by_category[category] = price
        else:
            spendings_by_category[category] += price

    # Format spendings by category
    category_spendings = ', '.join(f"{category} {amount}" for category, amount in spendings_by_category.items())

    report_message = f'You spent {total_spent} in {year}-{month:02d}. Your spendings: {category_spendings}.'
    bot.send_message(user_id, text=report_message)

    # Optionally, clear spendings from the database if needed
    # clear_query = "DELETE FROM spendings WHERE user_id = %s AND date >= %s AND date < %s"
    # cursor.execute(clear_query, (user_id, start_date, end_date))

