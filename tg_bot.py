from telegram import ext
from telegram import ReplyKeyboardMarkup
import dotenv
import redis

import logging
import os
from enum import IntEnum, unique

from common_functions import is_correct_answer


@unique
class Buttons(IntEnum):
    MENU = 0
    QUESTION = 1
    ANSWER = 2


def greet_user(bot, update):
    """Just hello message for /start command.

    :param bot: tg bot object
    :param update: event with update tg object
    :return: number of next action for conversation handler
    """
    custom_keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счёт']
    ]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    msg = 'Добро пожаловать в историческую викторину. Выберите действие!'
    bot.send_message(chat_id=update.message.chat_id, text=msg, reply_markup=reply_markup)

    return Buttons.MENU


def manage_menu_logic(bot, update, user_data):
    """Manage menu logic.

    :param bot: tg bot object
    :param update: event with update tg object
    :param user_data: users data which tg must remember. Dict-like interface
    :return: number of next action for conversation handler
    """
    if update.message.text == 'Новый вопрос':
        return Buttons.QUESTION

    if update.message.text == 'Сдаться':
        return Buttons.MENU


def give_question(bot, update, user_data):
    """Send any question.

    :param bot: tg bot object
    :param update: event with update tg object
    :param user_data: users data which tg must remember. Dict-like interface
    :return: number of next action for conversation handler
    """
    q = DB.randomkey().decode('utf-8')
    bot.send_message(chat_id=update.message.chat_id, text=q)

    answer = DB.get(q).decode('utf-8')
    user_data['answer'] = answer

    return Buttons.ANSWER


def check_answer(bot, update, user_data):
    """Check user answer.

    :param bot: tg bot object
    :param update: event with update tg object
    :param user_data: users data which tg must remember. Dict-like interface
    :return: number of next action for conversation handler
    """
    answer = user_data['answer']

    user_answer = update.message.text

    # half correct words is OK
    if is_correct_answer(user_answer, answer, limit=0.5):
        msg = 'Правильно! Полный ответ:\n{}\nХотите новый вопрос? Выберите в меню.'.format(user_data['answer'])
        bot.send_message(chat_id=update.message.chat_id, text=msg)
        return Buttons.QUESTION

    if update.message.text == 'Сдаться':
        msg = 'Жаль... Правильный ответ:\n{}\nХотите новый вопрос? Выберите в меню.'.format(user_data['answer'])
        bot.send_message(chat_id=update.message.chat_id, text=msg)
        return Buttons.QUESTION

    msg = 'К сожалению нет! Правильный ответ:\n{}\nХотите новый вопрос? Выберите в меню.'.format(user_data['answer'])
    bot.send_message(chat_id=update.message.chat_id, text=msg)
    return Buttons.QUESTION


def stop_quiz(bot, update):
    """Action which executes if user stop quiz.

    :param bot: tg bot object
    :param update: event with update tg object
    :return: number of next action for conversation handler
    """
    bot.send_message(chat_id=update.message.chat_id, text='Викторина остановлена.')

    return Buttons.MENU


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s  %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('tg_bot')

    dotenv.load_dotenv()
    TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
    PROXY = os.getenv('PROXY')  # Fill in .env if you are from mother Russia
    REDIS_DB_ADDRESS = os.getenv('REDIS_DB_ADDRESS')
    REDIS_DB_PORT = os.getenv('REDIS_DB_PORT')
    REDIS_DB_PASSWORD = os.getenv('REDIS_DB_PASSWORD')
    logger.debug('.env was read')

    DB = redis.Redis(host=REDIS_DB_ADDRESS, port=REDIS_DB_PORT, password=REDIS_DB_PASSWORD)

    # handler of bot's states
    conv_handler = ext.ConversationHandler(
        entry_points=[ext.CommandHandler('start', greet_user)],
        states={
            Buttons.MENU: [ext.MessageHandler(ext.Filters.text, manage_menu_logic, pass_user_data=True)],
            Buttons.QUESTION: [ext.MessageHandler(ext.Filters.text, give_question, pass_user_data=True)],
            Buttons.ANSWER: [ext.MessageHandler(ext.Filters.text, check_answer, pass_user_data=True)],
        },
        fallbacks=[ext.CommandHandler('stop', stop_quiz)]
    )

    request_kwargs = None
    if PROXY is not None:
        request_kwargs = {'proxy_url': PROXY}
    updater = ext.Updater(token=TG_BOT_TOKEN, request_kwargs=request_kwargs)

    # add handlers
    updater.dispatcher.add_handler(conv_handler)

    while True:
        try:
            updater.start_polling()
        except Exception:
            logger.exception('Critical error in ')
