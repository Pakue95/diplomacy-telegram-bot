# Diplomacy Telegram Bot

A simple Telegram bot that allows you to play a in-person game of Diplomacy. The bot manages "conference groupings", where countries are randomly assigned into one to three groupings.
Each group has then time to do their talks in seperate rooms until the timer has run out.

## Usage

Get yourself a bot and its token from the Telegram [BotFather](https://telegram.org/faq#q-how-do-i-create-a-bot) and save the token to `token.txt`. Invite the bot and the players into a new telegram group and run the bot:

```
poetry install
poetry run main.py
```

or (needs [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot))

```
python main.py
```

Use the telegram bot commands ("/...") to start/stop/edit the current session

Mind you the bot doesn't keep a state, so once it is restarted all countries are back in their original configuration.
