"""
Admin API calls
"""
import logging
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from stoscbots.util import bot_auth
import configparser
from stoscbots.util.loggers import LOGLEVEL
from stoscbots.db import db
from stoscbots.util import loggers, utils


logger = logging.getLogger('Handler.Main')
logger.setLevel(LOGLEVEL)
VIBIN_TELEGRAM_ID = int(os.environ.get('VIBIN_TELEGRAM_ID'))

@Client.on_message(filters.command(["version","ver"]))
@loggers.async_log_access
@bot_auth.async_management_only
async def version_handler(client: Client, message: Message):

    config = configparser.ConfigParser()
    config.read(r'.VERSION')
    msg = f"Telegram Version: **{message._client.APP_VERSION}** on **{message._client.SYSTEM_VERSION}**"
    msg += f"\nSession Name: **{client.name}**\n"
    msg += "-------------"
    msg += f"\nRelease Version: `{config.get('version', 'VERSION')}`"
    msg += f"\nRelease Date: `{config.get('version', 'RELEASE_DATE')}`"
    msg += f"\nBuild SHA: `{config.get('version', 'BUILD')[:7]}`"
    msg += f"\nBranch: `{config.get('version', 'BRANCH')}`"
    
    await message.reply_text(msg)


# -------------------------------------------------
# Add user via command
# /add 6109146073 F004 John Mathew
@Client.on_message(filters.command(["add"]))
@loggers.async_log_access
async def add_user_handler(client: Client, message: Message):
    # Only allow the bot owner to add users
    if message.from_user.id != VIBIN_TELEGRAM_ID:
        msg = "You are not allowed to add users"
        await message.reply_text(msg)
        return
    if len(message.command) < 4:
        msg = "Please enter proper commands\ne.g. `/add [telegram_id] [member_code] [name]`"
        await message.reply_text(msg)
        return
    else:
        telegram_id, member_code = message.command[1:3]
        name = ' '.join(message.command[3:])
        if utils.is_valid_member_code(member_code):
            # Add user to DB
            result = db.add_user(telegram_id, member_code, name)
            if result == 500:
                msg = f"Member already exists: `{name}({member_code})`"
                await message.reply_text(msg)
            elif result == 200:
                msg = f"User `{name}({member_code})` added successfully"
                await message.reply_text(msg)
            else:
                msg = f"Error adding user `{name}({member_code})`"
                await message.reply_text(msg)

# -------------------------------------------------
# Get a users Telegram ID
# /user V019
@Client.on_message(filters.command(["id"]))
@loggers.async_log_access
async def get_telegram_id_handler(client: Client, message: Message):
    # Only allow the bot owner to add users
    if message.from_user.id != VIBIN_TELEGRAM_ID:
        msg = "You are not allowed to execute this command"
        await message.reply_text(msg)
        return
    if len(message.command) < 2:
        msg = "Please enter proper commands\ne.g. `/add [member_code]`"
        await message.reply_text(msg)
        return
    else:
        member_code = message.command[1]
        if utils.is_valid_member_code(member_code):
            # Get the members Telegram ID by looking up in DyanmoDB
            result = utils.get_TelegramID_from_MemberCode(member_code.upper())
            if result:
                msg = f"**Member Details ({member_code})**\n"
                for entry in result:
                    msg += f"{entry['Name']}: `{entry['telegram_id']}`\n"
                await message.reply_text(msg)
            else:
                msg = f"Member not found: `{member_code}`"
                await message.reply_text(msg)
        else:
            msg = f"Invalid member code: `{member_code}`"
            await message.reply_text(msg)
            return

# -------------------------------------------------
# Send a Telegram message to a member
# /send 21999999 Hello World
@Client.on_message(filters.command(["send"]))
@loggers.async_log_access
async def send_msg(client: Client, message: Message):
    # Only allow the bot owner to add users
    if message.from_user.id != VIBIN_TELEGRAM_ID:
        msg = "You are not allowed to execute this command"
        await message.reply_text(msg)
        return
    if len(message.command) < 3:
        msg = "Please enter proper commands\ne.g. `/send [telegram_id] [message]`"
        await message.reply_text(msg)
        return
    else:
        telegram_id = message.command[1]
        msg = ' '.join(message.command[2:])
        _member_code = utils.getMemberCode_from_TelegramID(telegram_id)
        if telegram_id.isdigit() and utils.is_valid_member_code(_member_code):
            # Send the message to the user
            await client.send_message(telegram_id, msg)
            log_msg = f"Telegram message [`{msg}`] sent to `{telegram_id}` ({_member_code})"
            logger.info(log_msg)
            await message.reply_text(log_msg)