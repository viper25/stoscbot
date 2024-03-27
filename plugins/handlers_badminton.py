"""
To schedule badminton games
"""
import logging
import os

from pyrogram import Client, filters
from pyrogram.types import Message
from tabulate import tabulate

from stoscbots.util.badminton_util import generate_badminton_doubles_schedule, get_image
from stoscbots.util import bot_auth
from stoscbots.util import loggers
from stoscbots.util.loggers import LOGLEVEL

logger = logging.getLogger('Handler.Badminton')
logger.setLevel(LOGLEVEL)
VIBIN_TELEGRAM_ID = int(os.environ.get('VIBIN_TELEGRAM_ID'))
SIMON_TELEGRAM_ID = int(os.environ.get('SIMON_TELEGRAM_ID'))

# /game 20, Vibin, Jubin, Simon, Ajsh, Vinct, Liju, Jithin, Prdip, Vibin
@Client.on_message(filters.command(["game"]))
@loggers.async_log_access
@bot_auth.async_management_only
async def badminton_scheduler(client: Client, message: Message):
    if message.from_user.id not in [VIBIN_TELEGRAM_ID, SIMON_TELEGRAM_ID]:
        msg = "You are not allowed to use this function"
        await message.reply_text(msg)
        return
    if len(message.command) < 3:
        msg = "Please enter min arguments\ne.g. `/game [minutes] [PLAYER1, PLAYER2,...]`"
        await message.reply_text(msg)
        return
    else:
        num_matches = int(message.command[1])

        _players = ','.join(message.command[2:])
        # Splitting the combined string on commas to get individual player names
        players = [player.strip() for player in _players.split(',') if player.strip()]
        player_count = len(players)

        try:
            schedule = generate_badminton_doubles_schedule(players, num_matches)
            img = get_image([match[0] for match in schedule])
        except ValueError as e:
            logger.error(e)
            await message.reply_text(e)
            return

        await message.reply_photo(photo=img)

        # # Display the schedule in table format
        # table_data = []
        # for i, match in enumerate(schedule):
        #     table_data.append([i + 1, ', '.join(match[0])])
        # msg_parts = tabulate(table_data, headers=["#", "Players"], tablefmt="rst")
        # msg = f"`{msg_parts}`"
        # await message.reply_text(msg)

