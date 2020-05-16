# Quiz bots (VK and telegram) with Redis DB.

This project contains code for creation your bots in VK and Telegram.

Both, VK and Telegram bots are integrated with Redis DB.

### How to install

##### Local

You need to create `.env` file and write next parameters in file:

`TG_BOT_TOKEN` - secret telegram bot token. Use [this](https://core.telegram.org/bots#creating-a-new-bot) instruction (use VPN to open this link in Russia).

After you got `TG_BOT_TOKEN` you need to write to you telegram bot any message (`/start` for example).
    
`VK_APP_TOKEN` - secret VK app token. You can create it in group's administration panel (section `Work with API`).

`PROXY` - proxy IP with port and https if you need. Work with empty proxy if you in Europe.

`REDIS_DB_ADDRESS` - register your [redis](https://redislabs.com/) account and get address of your base (for example `redis-13965.f18.us-east-4-9.wc1.cloud.redislabs.com`).

`REDIS_DB_PORT` - usually port writes in db address in the end `redis-13965.f18.us-east-4-9.wc1.cloud.redislabs.com:16635`

`REDIS_DB_PASSWORD` - redis also will generate your DB password when your will init DB.

`DB_PATH` - path to file with questions and answers (default: `data\question.json`).

`DB_RECORD_COUNT` - count of questions which will write into DB (default: 100).

`REDIS_SET_OF_QUESTIONS_NAME` - name of redis set of questions. (default: QuestionAnswerSet)

`REDIS_HASH_OF_QUESTIONS_AND_ANSWERS_NAME` - name of redis hash of questions and answers. (default: QuestionAnswerHash)

`REDIS_HASH_USERS_INFO_NAME` - name of redis hash of users info for VK bot. (default: UsersHash)

Python3 should be already installed. 
Then use `pip` (or `pip3`, if there is a conflict with Python2) to install dependencies:
```
pip install -r requirements.txt
```

##### Deploy on heroku

For deploying this bot on [heroku](https://heroku.com) you need to do next:

1) Sign up in heroku
2) Create app
3) Clone this repository and download on heroku with GitHub method (tab `Deploy` in heroku app)
    
### How to use

##### Run in Local

Create your own `DB_PATH` file with training questions and answers.

Example of file:

```json
{
"data": {
    "1": {"q": "question", "a": "answer"},
    ...,
    "100": {"q": "question", "a": "answer"}
    },
"min_id": 1,
"max_id": 100
}
```

In file `redis_base_init.py` given a simple example of DB filling

Open command line (in windows `Win+R` and write `cmd` and `Ok`). Go to directory with program or write in cmd:

```
// filling your DB (file "question.json" must be in "data" subdirectory).
python redis_base_init.py 
```

```
// if you want to start telegram bot.
python tg_bot.py 
```
```
// if you want to start vk bot.
python vk_bot.py
```

##### Deploy on heroku

Run bot in `Resources` tab in heroku app. `Procfile` for run in repo already.

### References

- [telegram bots documentation](https://core.telegram.org/bots#creating-a-new-bot)
- [heroku](https://heroku.com)
- [VK API documentation](https://vk.com/dev/first_guide)
- [dialogflow documentation](https://cloud.google.com/dialogflow/docs/)
- [redis](https://redislabs.com/)

### Project Goals

The code is written for educational purposes on online-course for web-developers [dvmn.org](https://dvmn.org/).
