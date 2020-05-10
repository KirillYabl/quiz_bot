# Quiz bots (VK and telegram) with Redis DB.

This project contain code for create your bots in VK and Telegram.

Both, VK in Telegram bots are integrated with Redis DB.

### How to install

##### Local

You need to create `.env` file and write in file parameters:

`TG_BOT_TOKEN` - secret token for your telegram bot. Just use [this](https://core.telegram.org/bots#creating-a-new-bot) instruction (use VPN to open this link in Russia).

After you got `TG_BOT_TOKEN` you need to write to you bot in telegram any message (`/start` for example).
    
`VK_APP_TOKEN` - secret token of you VK app. You can create this in group administration panel in `Work with API`.

`PROXY` - proxy IP with port and https if you need. Work with empty proxy if you in Europe.

`REDIS_DB_ADDRESS` - register your account in [redis](https://redislabs.com/) and get address of your base (for example `redis-13965.f18.us-east-4-9.wc1.cloud.redislabs.com`).

`REDIS_DB_PORT` - usually port writes in db address in the end `redis-13965.f18.us-east-4-9.wc1.cloud.redislabs.com:16635`

`REDIS_DB_PASSWORD` - redis also will generate your DB password when your will init DB.

`DB_PATH` - path to file with questions and answer (default: `data\question.json`).

`DB_RECORD_COUNT` - count of question which will write to db (default: 100).

`REDIS_SET_OF_QUESTIONS_NAME` - name of redis set of questions. (default: QuestionAnswerSet)

`REDIS_HASH_OF_QUESTIONS_AND_ANSWERS_NAME` - name of redis hash of questions and answers. (default: QuestionAnswerHash)

`REDIS_HASH_USERS_INFO_NAME` - name of redis hash of users info for VK bot. (default: UsersHash)

Python3 should be already installed. 
Then use `pip` (or `pip3`, if there is a conflict with Python2) to install dependencies:
```
pip install -r requirements.txt
```

##### Deploy on heroku

For deploy this bot on [heroku](https://heroku.com) you need to do next:

1) Sign up in heroku
2) Create app
3) Clone this repository and download on heroku with GitHub method (tab `Deploy` in heroku app)
    
### How to use

##### Run in Local

Open command line (in windows `Win+R` and write `cmd` and `Ok`). Go to directory with program or just write in cmd:

Create your own `DB_PATH` file with training questions and answers for dialogflow.

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

```
// filling your DB (file "question.json" must be in "data" subdirectory).
python <PATH TO PROGRAM>\redis_base_init.py 
```

```
// if you want to start telegram bot.
python <PATH TO PROGRAM>\tg_bot.py 
```
```
// if you want to start vk bot.
python <PATH TO PROGRAM>\vk_bot.py
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
