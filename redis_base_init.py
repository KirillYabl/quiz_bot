import dotenv
import redis

import logging
import os
import json
import random


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s  %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('redis')

    dotenv.load_dotenv()
    REDIS_DB_ADDRESS = os.getenv('REDIS_DB_ADDRESS')
    REDIS_DB_PORT = os.getenv('REDIS_DB_PORT')
    REDIS_DB_PASSWORD = os.getenv('REDIS_DB_PASSWORD')

    with open('data/questions.json', encoding='utf-8') as f:
        data = json.load(f)
    data = {'data': data}
    data_keys = [int(num) for num in list(data['data'].keys())]
    data['min_id'] = min(data_keys)
    data['max_id'] = max(data_keys)
    logger.debug(f'data was reading. Min_id: {data["min_id"]}. Max_id: {data["max_id"]}')

    r = redis.Redis(host=REDIS_DB_ADDRESS, port=REDIS_DB_PORT, password=REDIS_DB_PASSWORD)
    new_data = False
    for i in range(100):
        q_num = str(random.randint(data['min_id'], data['max_id']))
        q = u'{}'.format(data['data'][q_num]['q'])
        a = u'{}'.format(data['data'][q_num]['a'])
        if new_data:
            r.append(q, a)
    q = r.randomkey().decode('utf-8')
    a = r.get(q).decode('utf-8')
    print(q)
    print(a)
    print(r.dbsize())
    r.close()
