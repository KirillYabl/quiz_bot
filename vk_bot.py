import random
import logging
import os
import json

import dotenv
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import redis

from common_functions import is_correct_answer

logger = logging.getLogger(__name__)


class VkSessionUsersCondition:
    """User DB in Redis.

    Usage:
        For queries economy purpose
        1. ALWAYS get user_info
        2. Do other operations

    :param redis_db: object of connection redis db
    :param name_of_hash: str, name of your hash in redis
    """

    def __init__(self, redis_db, name_of_hash):
        # Template of info about new user
        self.new_user_template = json.dumps({
            'got_q': False,  # Is user got question
            'q': '',  # text of question
            'a': ''  # text of answer
        })
        self.redis_db = redis_db
        self.name_of_hash = name_of_hash
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug('Class params were initialized')

    def add_or_update_user(self, user_id, user_info=None):
        """Add new user or update existing user if he got answer.

        :param user_id: id of user in VK
        :param user_info: dict or None, if don't need template
        """
        if user_info is None:
            self.redis_db.hset(self.name_of_hash, user_id, self.new_user_template)
            self.logger.debug(f'User created, user_id={user_id}')
            return

        dumped_user_info = json.dumps(user_info)
        self.redis_db.hset(self.name_of_hash, user_id, dumped_user_info)
        self.logger.debug(f'User updated, user_id={user_id}')
        return

    def get_user_info(self, user_id):
        """Get user info by user_id, convert to JSON if user in db.

        :param user_id: id of user in VK
        :return: bool, True if user found
        """
        user_info = self.redis_db.hget(self.name_of_hash, user_id)

        if user_info is not None:
            user_info = json.loads(user_info).decode('utf-8')

        return user_info

    def is_user_got_question(self, user_id, user_info):
        """Check status of user question.

        :param user_id: id of user in VK
        :return: bool, True if user got question
        """
        if user_info is None:
            self.add_or_update_user(user_id)
            return False
        return user_info['got_q']

    def get_user_correct_answer(self, user_id, user_info):
        """Get user correct answer.

        If this method gave answer, user will update.
        If this method didn't know user, user will initialize. And method will return 'None' for the next handling.
        If user didn't get question, method will return 'None' for the next handling.

        :param user_id: id of user in VK
        :param user_info: dict or None, if don't need template
        :return: answer or None (don't know user or user didn't get question)
        """

        if user_info is None:
            self.add_or_update_user(user_id)
            return None

        if user_info['got_q']:
            answer = user_info['a']
            self.add_or_update_user(user_id)
            return answer
        return None

    def add_answer_to_user(self, user_id, user_info, question, answer):
        """Update user with new answer.

        :param user_id: id of user in VK
        :param user_info: dict or None, if don't need template
        :param question: str, user question
        :param answer: str, correct answer
        """

        if user_info is None:
            self.add_or_update_user(user_id)

        user_info['got_q'] = True
        user_info['q'] = question
        user_info['a'] = answer
        self.add_or_update_user(user_id, user_info)
        self.logger.debug(f'User got answer and updated, user_id={user_id}')


def init_keyboard():
    """Initialize keyboard.

    :return: keyboard object
    """
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)

    logger.debug('Keyboard initialized')
    return keyboard


def give_up(event, vk_api, **kwargs):
    """Button give up logic.

    :param event: event which discribe message
    :param vk_api: authorized session in vk
    :param kwargs: dict, named args
    :return: str, type of answer
    """
    answer = kwargs['answer']
    msg = kwargs['msg']

    if answer is None:
        msg += 'Еще не получили вопрос, а уже сдаетесь? Попробуйте сыграть в викторину.\n'
        msg += 'Нажмите на кнопку "Новый вопрос".'
        vk_api.messages.send(
            user_id=event.user_id,
            message=msg,
            random_id=random.randint(1, 1000),
            keyboard=init_keyboard().get_keyboard()
        )
        return 'give up without question'

    msg = f'Жаль, правильный ответ:\n{answer}'
    vk_api.messages.send(
        user_id=event.user_id,
        message=msg,
        random_id=random.randint(1, 1000),
        keyboard=init_keyboard().get_keyboard()
    )
    return 'give up'


def new_question_old_user(event, vk_api, **kwargs):
    """Button new question logic in situation where user got questions early.

    :param event: event which discribe message
    :param vk_api: authorized session in vk
    :param kwargs: dict, named args
    :return: str, type of answer
    """
    msg = kwargs['msg']
    answer = kwargs['answer']
    new_q = kwargs['q']

    msg += f'А как же предыдущий вопрос?\nПравильный ответ:\n{answer}'
    vk_api.messages.send(
        user_id=event.user_id,
        message=msg,
        random_id=random.randint(1, 1000),
        keyboard=init_keyboard().get_keyboard()
    )
    msg = f'Ваш новый вопрос:\n{new_q}'
    vk_api.messages.send(
        user_id=event.user_id,
        message=msg,
        random_id=random.randint(1, 1000),
        keyboard=init_keyboard().get_keyboard()
    )
    return "new question for old user without answer previous"


def new_question_new_user(event, vk_api, **kwargs):
    """Button new question logic for new user.

    :param event: event which discribe message
    :param vk_api: authorized session in vk
    :param kwargs: dict, named args
    :return: str, type of answer
    """
    msg = kwargs['msg']
    new_q = kwargs['q']

    msg += new_q
    vk_api.messages.send(
        user_id=event.user_id,
        message=msg,
        random_id=random.randint(1, 1000),
        keyboard=init_keyboard().get_keyboard()
    )
    return 'new question for new user'


def check_answer(event, vk_api, **kwargs):
    """Logic of checking answers.

    :param event: event which discribe message
    :param vk_api: authorized session in vk
    :param kwargs: dict, named args
    :return: str, type of answer
    """
    correct_answer = kwargs['correct_answer']

    if is_correct_answer(event.text, correct_answer, limit=0.5):
        msg = f'Правильно! Полный ответ:\n{correct_answer}\nХотите новый вопрос? Выберите в меню.'
        type_of_answer = 'correct answer'
    else:
        msg = f'К сожалению нет! Полный ответ:\n{correct_answer}\nХотите новый вопрос? Выберите в меню.'
        type_of_answer = 'incorrect answer'

    vk_api.messages.send(
        user_id=event.user_id,
        message=msg,
        random_id=random.randint(1, 1000),
        keyboard=init_keyboard().get_keyboard()
    )
    return type_of_answer


def send_new_question_msg(event, vk_api, **kwargs):
    """Send recommendation to press button 'new question'.

    :param event: event which discribe message
    :param vk_api: authorized session in vk
    :param kwargs: dict, named args
    :return: str, type of answer
    """
    msg = kwargs['msg']

    msg += 'Нажмите на кнопку "Новый вопрос" для получения вопроса.'
    vk_api.messages.send(
        user_id=event.user_id,
        message=msg,
        random_id=random.randint(1, 1000),
        keyboard=init_keyboard().get_keyboard()
    )
    return 'press new question'


def run_bot_logic(event, vk_api, redis_db, users_db, redis_set_name, redis_hash_name):
    """Logic of bot.

    :param event: event which discribe message
    :param vk_api: authorized session in vk
    :param redis_db: redis DB with questions
    :param users_db: custom DB of users condition
    """
    first_time = False
    got_question = True
    msg = ''

    if not (event.type == VkEventType.MESSAGE_NEW and event.to_me):
        return

    logger.debug(f'Starting work. user_id={event.user_id}')
    # in start we will get future question and answer if didn't get early
    user_info = users_db.get_user_info(event.user_id)
    if user_info is None:
        users_db.add_or_update_user(event.user_id)
        first_time = True
        msg += 'Рады приветствовать вас в нашей викторине!\n'
        logger.debug('User play first time.')

    if not users_db.is_user_got_question(event.user_id, user_info):
        got_question = False
        logger.debug('User didn\'t get question.')

    if event.text == "Сдаться":
        logger.debug('User gave up')
        answer = users_db.get_user_correct_answer(event.user_id, user_info)
        type_of_answer = give_up(event, vk_api, answer=answer, msg=msg)
        logger.debug(f'"{type_of_answer}" message were sent')
        return
    elif event.text == "Новый вопрос":
        logger.debug('User is getting new question')

        # user isn't playing first time. But he pressed "new question" instead answer to question
        if got_question and not first_time:
            answer = users_db.get_user_correct_answer(event.user_id, user_info)
            new_q = redis_db.srandmember(redis_set_name, 1)[0].decode('utf-8')
            new_answer = redis_db.hget(redis_hash_name, new_q).decode('utf-8')
            users_db.add_answer_to_user(event.user_id, user_info, new_q, new_answer)
            type_of_answer = new_question_old_user(event, vk_api, answer=answer, new_q=new_q, msg=msg)
            logger.debug(f'"{type_of_answer}" message were sent')
            return

        # user is playing first time
        new_q = redis_db.srandmember(redis_set_name, 1)[0].decode('utf-8')
        new_answer = redis_db.hget(redis_hash_name, new_q).decode('utf-8')
        users_db.add_answer_to_user(event.user_id, user_info, new_q, new_answer)
        type_of_answer = new_question_new_user(event, vk_api, new_q=new_q, msg=msg)
        logger.debug(f'"{type_of_answer}" message were sent')
        return
    else:
        # user got question and he is trying answer
        if got_question:
            correct_answer = users_db.get_user_correct_answer(event.user_id, user_info)
            type_of_answer = check_answer(event, vk_api, correct_answer=correct_answer)
            logger.debug(f'"{type_of_answer}" message were sent')
            return

        # user didn't get question and bot must get recommendation to press 'new question' button
        type_of_answer = send_new_question_msg(event, vk_api, msg=msg)
        logger.debug(f'"{type_of_answer}" message were sent')
        return


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s  %(message)s', level=logging.DEBUG)

    dotenv.load_dotenv()
    vk_app_token = os.getenv('VK_APP_TOKEN')
    redis_db_address = os.getenv('REDIS_DB_ADDRESS')
    redis_db_port = os.getenv('REDIS_DB_PORT')
    redis_db_password = os.getenv('REDIS_DB_PASSWORD')
    redis_set_of_questions_name = os.getenv('REDIS_SET_OF_QUESTIONS_NAME')
    redis_hash_of_questions_and_answers_name = os.getenv('REDIS_HASH_OF_QUESTIONS_AND_ANSWERS_NAME')
    redis_hash_users_info_name = os.getenv('REDIS_HASH_USERS_INFO_NAME')
    logger.debug('.env were read')

    if redis_set_of_questions_name is None:
        redis_set_of_questions_name = 'QuestionAnswerSet'
    if redis_hash_of_questions_and_answers_name is None:
        redis_hash_of_questions_and_answers_name = 'QuestionAnswerHash'
    if redis_hash_users_info_name is None:
        redis_hash_users_info_name = 'UsersHash'

    redis_db = redis.Redis(host=redis_db_address, port=redis_db_port, password=redis_db_password)
    logger.debug('Got DB connection')
    users_db = VkSessionUsersCondition(redis_db, redis_hash_users_info_name)

    while True:
        try:
            vk_session = vk.VkApi(token=vk_app_token)
            logger.debug('Got VK API connection')
            vk_api = vk_session.get_api()
            longpoll = VkLongPoll(vk_session)
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    run_bot_logic(event, vk_api, redis_db, users_db, redis_set_of_questions_name,
                                  redis_hash_of_questions_and_answers_name)
        except Exception:
            logger.exception('Critical error in ')
