import telebot

def get_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup()
    button = telebot.types.InlineKeyboardButton('Weather in a city', callback_data='weather')
    button2 = telebot.types.InlineKeyboardButton('Spendings', callback_data='spendings')
    button3 = telebot.types.InlineKeyboardButton('Remiders and Schedule', callback_data='remind')
    button4 = telebot.types.InlineKeyboardButton('ChatGPT', callback_data='GPT')
    button5 = telebot.types.InlineKeyboardButton('Get a picture', callback_data='paint')
    keyboard.add(button)
    keyboard.add(button2)
    keyboard.add(button3)
    keyboard.add(button4)
    keyboard.add(button5)
    return keyboard

def R_or_S():
    keyboard = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton('Make a schedule', callback_data='Schedule')
    button2 = telebot.types.InlineKeyboardButton('Make a reminder', callback_data='Reminder')
    keyboard.add(button1, button2)
    return keyboard