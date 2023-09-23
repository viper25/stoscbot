"""
To schedule badminton games
"""
import logging
import os

from pyrogram import Client, filters
from pyrogram.types import Message
from tabulate import tabulate

from plugins.badminton_util import generate_badminton_doubles_schedule
from stoscbots.util import bot_auth
from stoscbots.util import loggers
from stoscbots.util.loggers import LOGLEVEL

logger = logging.getLogger('Handler.Badminton')
logger.setLevel(LOGLEVEL)
VIBIN_TELEGRAM_ID = int(os.environ.get('VIBIN_TELEGRAM_ID'))
SIMON_TELEGRAM_ID = int(os.environ.get('SIMON_TELEGRAM_ID'))
JOSEY_TELEGRAM_ID = int(os.environ.get('JOSEY_TELEGRAM_ID'))
DON_TELEGRAM_ID = int(os.environ.get('DON_TELEGRAM_ID'))
SAJAN_TELEGRAM_ID = int(os.environ.get('SAJAN_TELEGRAM_ID'))
AVG_TIME_PER_MATCH = (10 + 14) // 2  # Average between 10 and 14 minutes per match


# /game 20, Vibin, Jubin, Simon, Ajsh, Vinct, Liju, Jithin, Prdip, Vibin, Dibu
@Client.on_message(filters.command(["game"]))
@loggers.async_log_access
@bot_auth.async_management_only
async def badminton_scheduler(client: Client, message: Message):
    if message.from_user.id != VIBIN_TELEGRAM_ID:
        msg = "You are not allowed to add users"
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

        schedule, player_count = generate_badminton_doubles_schedule(players, num_matches)

        # Display the schedule in table format
        table_data = []
        for i, match in enumerate(schedule):
            table_data.append([i + 1, '|'.join(match[0]), '|'.join(match[1])])
        msg_parts = [tabulate(table_data, headers=["#", "Team 1", "Team 2"], tablefmt="orgtbl")]

        msg_parts.append("\n\n**Player Participation Counts**")
        data = [(player, count) for player, count in player_count.items()]
        msg_parts.append(tabulate(data, headers=['Player', 'Games'], tablefmt="simple"))

        # Add ticks to the tables to make it mono-spaced
        msg_parts[0] = f"`\n{msg_parts[0]}`"
        msg_parts[2] = f"`\n{msg_parts[2]}`"

        msg = '\n'.join(msg_parts)

        await message.reply_text(msg)
