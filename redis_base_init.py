import dotenv
import redis

import logging
import os
import json

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s  %(message)s', level=logging.DEBUG)

    dotenv.load_dotenv()
    redis_db_address = os.getenv('REDIS_DB_ADDRESS')
    redis_db_port = os.getenv('REDIS_DB_PORT')
    redis_db_password = os.getenv('REDIS_DB_PASSWORD')
    questions_db_path = os.getenv('QUESTIONS_DB_PATH', default='data/questions.json')
    db_record_count = os.getenv('DB_RECORD_COUNT', default=100)
    redis_set_of_questions_name = os.getenv('REDIS_SET_OF_QUESTIONS_NAME', default='QuestionAnswerSet')
    redis_hash_of_questions_and_answers_name = os.getenv('REDIS_HASH_OF_QUESTIONS_AND_ANSWERS_NAME',
                                                         default='QuestionAnswerHash')

    logger.debug('.env was read')

    with open(db_path, encoding='utf-8') as f:
        data = json.load(f)
    logger.debug(f'data was read. Length: {len(data)}')

    redis_db = redis.Redis(host=redis_db_address, port=redis_db_port, password=redis_db_password)

    for questions_answer_num, question_data in enumerate(data.items()):
        # all data can be very bigger for DB and maybe you don't want upload all data
        if questions_answer_num == db_record_count:
            break

        question_num, question_answer = question_data
        question = str(question_answer['q']).encode('utf-8')
        answer = str(question_answer['a']).encode('utf-8')

        redis_db.hset(redis_hash_of_questions_and_answers_name, question, answer)
        redis_db.sadd(redis_set_of_questions_name, question)
        logger.debug(f'Question {question_num} was record in DB')

    logger.debug(f'db size {redis_db.dbsize()}')
    redis_db.close()
