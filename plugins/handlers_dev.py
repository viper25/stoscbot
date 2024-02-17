"""
Admin API calls
"""
import configparser
import logging
import os
import platform
import subprocess

from pyrogram import Client, filters
from pyrogram.types import Message

from stoscbots.db import db
from stoscbots.util import bot_auth
from stoscbots.util import loggers, utils
from stoscbots.util.loggers import LOGLEVEL

logger = logging.getLogger('Handler.Main')
logger.setLevel(LOGLEVEL)


@Client.on_message(filters.command(["version", "ver"]))
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
    if bot_auth.is_super_admin(message.from_user.id) is False:
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
    if bot_auth.is_super_admin(message.from_user.id) is False:
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
    if bot_auth.is_super_admin(message.from_user.id) is False:
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


# -------------------------------------------------
# Get Server stats and Logs
# /cmd logs 1
@Client.on_message(filters.command(["cmd"]))
@loggers.async_log_access
async def run_commands(client: Client, message: Message):
    # Only allow the bot owner
    if not bot_auth.is_super_admin(message.from_user.id):
        await message.reply_text("You are not allowed to execute this command")
        return

    if len(message.command) < 2:
        await message.reply_text("Please enter proper commands\ne.g. `/cmd [command]`")
        return

    cmd_result = "No result"
    command = message.command[1]
    args = message.command[2:] if len(message.command) > 2 else None
    log_file_path = '/home/ubuntu/bots/stoscbot/logs/stosc_logs.log' if platform.system() == "Linux" else 'logs/vjk_logs.log'

    if command == 'logs':
        cmd_result = await handle_logs_command(args, log_file_path)

    await message.reply_text(f"`{cmd_result}`")

async def handle_logs_command(args, log_file_path):
    num_of_lines = 50
    if not os.path.exists(log_file_path):
        return "Log file does not exist."

    if args:
        if platform.system() == "Linux":
            cmd = f"tail -{num_of_lines}f {log_file_path} | grep {args[0]}"
            logger.info(f"Executing {cmd}")
            cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        else:  # Windows
            with open(log_file_path, 'r', encoding='utf-8') as file:
                cmd_result = [x for x in file.readlines()[-num_of_lines:] if args[0] in x]
        return '\n'.join(cmd_result)

    if platform.system() == "Linux":
        cmd = f"tail -{num_of_lines}f {log_file_path}"
        logger.info(f"Executing {cmd}")
        cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
    else:  # Windows
        with open(log_file_path, 'r', encoding='utf-8') as file:
            cmd_result = file.readlines()[-num_of_lines:]
    return '\n'.join(cmd_result)














async def run_commands_2(client: Client, message: Message):
    # Only allow the bot owner
    if bot_auth.is_super_admin(message.from_user.id) is False:
        msg = "You are not allowed to execute this command"
        await message.reply_text(msg)
        return
    if len(message.command) < 2:
        msg = "Please enter proper commands\ne.g. `/cmd [command]`"
        await message.reply_text(msg)
        return
    else:
        cmd_result = "No result"
        command = message.command[1]
        if len(message.command) > 2:
            args = message.command[2:]
        else:
            args = None

        if command == 'logs':
            num_of_lines = 50
            if args:
                if platform.system() == "Linux":
                    cmd = f"tail -{num_of_lines}f /home/ubuntu/bots/stoscbot/logs/stosc_logs.log | grep {args[0]}"
                    logger.info(f"Executing {cmd}")
                    cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                    # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    # output, error = process.communicate()
                    # cmd_result = output.decode('utf-8')
                    # error = error.decode('utf-8')


                elif platform.system() == "Windows":
                    # Show last 10 lines of log at logs/vjk_logs.log
                    with open('logs/vjk_logs.log', 'r', encoding='utf-8') as file:
                        cmd_result = file.readlines()[-num_of_lines:]
                        # Filter the lines with the search string
                        cmd_result = [x for x in cmd_result if args[0] in x]
                        cmd_result = '\n'.join(cmd_result)
            else:
                if platform.system() == "Linux":
                    cmd = f"tail -{num_of_lines}f /home/ubuntu/bots/stoscbot/logs/stosc_logs.log"
                    logger.info(f"Executing {cmd}")
                    cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                    # process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    # output, error = process.communicate()
                    # cmd_result = output.decode('utf-8')
                    # error = error.decode('utf-8')

                    cmd_result = cmd_result.stdout.split('\n')
                    cmd_result = '\n'.join(cmd_result)
                elif platform.system() == "Windows":
                    # Show last x lines of log at logs/vjk_logs.log
                    with open('logs/vjk_logs.log', 'r', encoding='utf-8') as file:
                        cmd_result = file.readlines()[-num_of_lines:]
                        cmd_result = '\n'.join(cmd_result)

        await message.reply_text(f"`{cmd_result}`")
