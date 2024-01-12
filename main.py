#!/usr/bin/env python

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from textwrap import dedent
import re
import random
import asyncio
from useless_comments import snarky_removed_country_comments, diplomacy_loading_messages


config = {
    "discussion_time_minutes": 10,
    # weights for the number of conferences to have two, three or all countries
    "conferences_weight": [0.6, 0.3, 0.1],
    "countries": [
        "Austria",
        "England",
        "France",
        "Germany",
        "Italy",
        "Russia",
        "Turkey",
    ],
    "country_emoji": {
        "Austria": "🇦🇹",
        "England": "󠁧󠁢󠁥󠁮󠁧󠁿🇬🇧",
        "France": "🇫🇷",
        "Germany": "🇩🇪",
        "Italy": "🇮🇹",
        "Russia": "🇷🇺",
        "Turkey": "🇹🇷",
    },
    "rooms": ["Room 1", "Room 2", "Room 3"],
}

with open("token.txt", "r") as f:
    config["bot_token"] = f.read().strip()

        
def game_state() -> str:
    out = "The currently active countries are: \n"
    out += ("\n").join(
        [
            "{} {}".format(config["country_emoji"].get(country, "🏳"), country)
            for country in config["countries"]
        ]
    )
    return out


async def start_useless(update: Update, context: ContextTypes) -> None:
    job_name = "useless_comment"
    await update.message.reply_text("Random Messages: On")

    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    if current_jobs:
        return

    context.job_queue.run_repeating(
        generate_useless_comment,
        600,
        name="useless_comment",
        chat_id=update.message.chat_id,
    )


async def stop_useless(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    job_name = "useless_comment"
    job = context.job
    await update.message.reply_text("Random Messages: Off")
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()


async def generate_useless_comment(context: ContextTypes.DEFAULT_TYPE):
    # a list of random useless comments for each country
    useless_comment = random.choice(diplomacy_loading_messages)

    await context.bot.send_message(context.job.chat_id, text=useless_comment)


def get_conference_pairings():
    num_conference = ["two", "three", "all"]
    num_conference_weights = config["conferences_weight"]
    num_conference = random.choices(num_conference, num_conference_weights)[0]

    if num_conference == "all":
        return config["countries"]
    if num_conference == "two":
        size = 2
    if num_conference == "three":
        size = 3

    random_ordered_countries = random.sample(
        config["countries"], len(config["countries"])
    )
    out = []
    for i in range(0, len(random_ordered_countries), size):
        out.append(random_ordered_countries[i : i + size])

    if len(out[-1]) == 1:
        out[-2].append(out[-1][0])
        out.pop()

    return out


async def remove_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    to_remove = re.sub(r"/\w+\s", "", update.message.text)
    if not to_remove in config["countries"]:
        await update.message.reply_text("Country not found")
        return

    config["countries"].remove(to_remove)
    await update.message.reply_text("Country removed \n" + game_state())
    await update.message.reply_text(
        random.choice(
            snarky_removed_country_comments.get(
                to_remove, snarky_removed_country_comments["Other"]
            )
        )
    )


async def add_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    to_add = re.sub(r"/\w+\s", "", update.message.text)
    if to_add in config["countries"]:
        await update.message.reply_text("Country already added")
        return

    if to_add == "/add":
        await update.message.reply_text("Please enter a country")
        return

    config["countries"].append(to_add)
    await update.message.reply_text("Country added \n" + game_state())


async def timer_done_conference(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send message on job completion."""
    job = context.job
    await context.bot.send_message(
        job.chat_id, text=f"Conference is over. Return to the kitchen!"
    )


async def start_conference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    job_name = "C"
    chat_id = update.effective_message.chat_id
    try:
        due = float(config["discussion_time_minutes"] * 60)

        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        if current_jobs:
            await update.effective_message.reply_text(f"Conference is already running!")
            return

        context.job_queue.run_once(
            timer_done_conference, due, chat_id=chat_id, name=job_name, data=due
        )

        pairs = get_conference_pairings()

        await update.effective_message.reply_text(f"Conference started! \n\nPairings:")

        for idx, pairing in enumerate(pairs):
            message = f"{config['rooms'][idx]}:\n"

            for country in pairing:
                message += f"{config['country_emoji'].get(country, '🏳️')} {country}\n"

            await update.effective_message.reply_text(message)

    except Exception as e:
        print(e)
        await update.effective_message.reply_text("Usage: /start")


async def stop_conference(update: Update, context: ContextTypes) -> None:
    job_name = "C"
    current_jobs = context.job_queue.get_jobs_by_name(job_name)

    if not current_jobs:
        await update.message.reply_text("No conference running")
        return

    for job in current_jobs:
        job.schedule_removal()

    await update.message.reply_text("Conference stopped")


async def help(update: Update, context: ContextTypes) -> None:
    message = dedent(
        """
    /start - start conference
    /stop - stop conference
    /add <country> - add country to list of countries
    /remove <country> - remove country from list of countries
    /set_timer_length <minutes> - set length of conference in minutes
    /help - show this help message
    /start_useless - start sending useless comments
    /stop_useless - stop sending useless comments
    /info - show current game state
    """
    ).strip("\n")
    await update.message.reply_text(message)


async def set_conference_length(update: Update, context: ContextTypes) -> None:
    print(update)
    string_num = re.sub(r"/\w+\s", "", update.message.text)

    try:
        num = int(string_num)
    except ValueError:
        await update.message.reply_text("Please enter a valid number")
        return

    if num <= 0:
        await update.message.reply_text("Please enter a positive number")
        return

    config["discussion_time_minutes"] = num

    await update.message.reply_text(f"Conference length set to {num} minute(s)")


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game_state_str = game_state()

    await update.message.reply_text(game_state_str)


if __name__ == "__main__":
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config["bot_token"]).build()

    application.add_handler(CommandHandler("start", start_conference))
    application.add_handler(CommandHandler("remove", remove_country))
    application.add_handler(CommandHandler("add", add_country))
    application.add_handler(CommandHandler("set_timer_length", set_conference_length))
    application.add_handler(CommandHandler("stop", stop_conference))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("start_useless", start_useless))
    application.add_handler(CommandHandler("stop_useless", stop_useless))
    application.add_handler(
        CommandHandler("info", info)
    )  # Add the info command handler

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        application.bot.set_my_commands(
            [
                ("start", "Start conference"),
                ("stop", "Stop conference"),
                ("add", "Add country to list of countries"),
                ("remove", "Remove country from list of countries"),
                ("set_timer_length", "Set length of conference in minutes"),
                ("help", "Show this help message"),
                ("start_useless", "Start sending useless comments"),
                ("stop_useless", "Stop sending useless comments"),
                ("info", "Show current game state"),
            ]
        )
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
