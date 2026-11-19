"""
Admin API calls
"""
import configparser
import datetime
import logging
import os
import platform
import subprocess
from datetime import datetime

from dateutil.relativedelta import relativedelta
from pyrogram import Client, filters
from pyrogram.errors import RichMessageUnsupported
from pyrogram.types import CallbackQuery, Message

from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import bot_auth, loggers, utils
from stoscbots.util.loggers import LOGLEVEL
from stoscbots.util.utils import format_telegram_message

logger = logging.getLogger('Handler.Main')
logger.setLevel(LOGLEVEL)

VIBIN_TELEGRAM_ID = int(os.environ.get('VIBIN_TELEGRAM_ID'))
STOSCBOT_APP_HOME_DIR = os.environ.get('STOSCBOT_APP_HOME_DIR')     # e.g. the vibinjk in '/home/vibinjk'

def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data), data=data
    )


# -------------------------------------------------
@Client.on_message(filters.command(["version", "ver"]))
@loggers.async_log_access
async def version_handler(client: Client, message: Message):
    config = configparser.ConfigParser()
    config.read(r'.VERSION')
    version_info = {
        "version": config.get("version", "VERSION", fallback="Unknown"),
        "release_date": config.get("version", "RELEASE_DATE", fallback="Unknown"),
        "build": config.get("version", "BUILD", fallback="Unknown")[:7],
        "branch": config.get("version", "BRANCH", fallback="Unknown"),
    }
    runtime_info = {
        "app_version": getattr(message._client, "APP_VERSION", "Unknown"),
        "system_version": getattr(message._client, "SYSTEM_VERSION", platform.system()),
        "python_version": platform.python_version(),
        "session_name": client.name or "stoscbot",
    }
    fallback = (
        f"Telegram Version: **{runtime_info['app_version']}** on **{runtime_info['system_version']}**\n"
        f"Session Name: **{runtime_info['session_name']}**\n"
        "-------------\n"
        f"Release Version: `{version_info['version']}`\n"
        f"Release Date: `{version_info['release_date']}`\n"
        f"Build SHA: `{version_info['build']}`\n"
        f"Branch: `{version_info['branch']}`"
    )
    chat_id = message.from_user.id
    try:
        rich_card = keyboards.get_rich_version_card(version_info, runtime_info)
        await client.send_rich_message(chat_id, rich_card, reply_markup=keyboards.back_to_main_keyboard)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected rich version card; sending plain text")
        await message.reply_text(fallback, reply_markup=keyboards.back_to_main_keyboard)


# -------------------------------------------------
# Add user via command
# /add 6109146073 F004 John Mathew
@Client.on_message(filters.command(["add"]))
@loggers.async_log_access
@bot_auth.super_admin_only
async def add_user_handler(client: Client, message: Message):
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
# /id V019
@Client.on_message(filters.command(["id"]))
@loggers.async_log_access
@bot_auth.super_admin_only
async def get_telegram_id_handler(client: Client, message: Message):
    if len(message.command) < 2:
        msg = "Please enter proper commands\ne.g. `/id [member_code]`"
        await message.reply_text(msg)
        return

    member_code = message.command[1].strip()
    if utils.is_valid_member_code(member_code):
        # Get the members Telegram ID by looking up in DynamoDB
        entries = utils.get_all_TelegramIDs_from_MemberCode(member_code.upper())
        if not entries:
            single = utils.get_TelegramID_from_MemberCode(member_code.upper())
            if single:
                entries = [single] if isinstance(single, dict) else single

        if entries:
            msg = f"**Member Details ({member_code.upper()})**\n"
            for entry in entries:
                name = entry.get('Name', 'Unknown')
                tid = entry.get('telegram_id', 'Unknown')
                msg += f"{name}: `{tid}`\n"
            await message.reply_text(msg)
        else:
            msg = f"Member not found: `{member_code.upper()}`"
            await message.reply_text(msg)
    else:
        msg = f"Invalid member code: `{member_code}`"
        await message.reply_text(msg)


# -------------------------------------------------
# Send a Telegram message to a member
# /send 21999999 Hello World
@Client.on_message(filters.command(["send"]))
@loggers.async_log_access
@bot_auth.super_admin_only
async def send_msg(client: Client, message: Message):
    if len(message.command) < 3:
        msg = "Please enter proper commands\ne.g. `/send [telegram_id] [message]`"
        await message.reply_text(msg)
        return

    telegram_id = message.command[1]
    msg = ' '.join(message.command[2:])

    if telegram_id.upper() == "ALL":
        # Get all members from the DB
        members = db.get_all_members_telegram_ids()

        # Calculate the date 3 months ago
        three_months_ago = datetime.datetime.now() - relativedelta(months=2)

        # Filter out members with 'last_seen' key and are recent
        recent_members = [d for d in members if 'last_seen' in d and
                          datetime.datetime.strptime(d['last_seen'], "%Y/%m/%d %H:%M:%S") > three_months_ago]

        for member in recent_members:
            # If environment is not production, set member = '000'
            if os.environ.get("ENV").upper() != 'PRO':
                member['telegram_id'] = int(os.environ.get('VIBIN_TELEGRAM_ID'))
            # Send the message to the user
            await client.send_message(int(member['telegram_id']), msg)
            log_msg = f"Telegram message [`{msg}`] sent to {member['Name']} ({member['member_code']})-{member['telegram_id']}"
            logger.info(log_msg)
        await message.reply_text(f"Message sent to {len(recent_members)} members")
    elif telegram_id.isdigit():
        _member_code = utils.getMemberCode_from_TelegramID(telegram_id)
        if utils.is_valid_member_code(_member_code):
            # Send the message to the user
            await client.send_message(telegram_id, msg)
            log_msg = f"Telegram message [`{msg}`] sent to `{telegram_id}` ({_member_code})"
            logger.info(log_msg)
            await message.reply_text(log_msg)
        else:
            await message.reply_text("Invalid Telegram ID")
    else:
        await message.reply_text("Invalid Telegram ID")


# -------------------------------------------------
# Get Server stats and Logs
# /cmd logs 1
@Client.on_message(filters.command(["cmd"]))
@loggers.async_log_access
@bot_auth.super_admin_only
async def run_commands(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Please enter proper commands\ne.g. `/cmd [command]`")
        return

    cmd_result = "No result"
    command = message.command[1]
    args = message.command[2:] if len(message.command) > 2 else None
    log_file_path = f"/home/{STOSCBOT_APP_HOME_DIR}/bots/stoscbot/logs/stosc_logs.log" if platform.system() == "Linux" else 'logs/vjk_logs.log'

    if command == 'logs':
        cmd_result = await handle_logs_command(args, log_file_path)

    await message.reply_text(f"`{format_telegram_message(cmd_result)}`")


async def handle_logs_command(args, log_file_path):
    num_of_lines = 30
    if not os.path.exists(log_file_path):
        return "Log file does not exist."

    if args:
        if platform.system() == "Linux":
            cmd = rf"tail -{num_of_lines} {log_file_path} | grep {args[0]} | grep -v '\[{VIBIN_TELEGRAM_ID}:vibinjk:Vibin\]'"
            logger.info(f"Executing {cmd}")
            cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        else:  # Windows
            with open(log_file_path, 'r', encoding='utf-8') as file:
                cmd_result = [x for x in file.readlines()[-num_of_lines:] if args[0] in x]
        return '\n'.join(cmd_result)

    if platform.system() == "Linux":
        cmd = rf"tail -{num_of_lines} {log_file_path} | grep -v '\[{VIBIN_TELEGRAM_ID}:vibinjk:Vibin\]'"
        logger.info(f"Executing {cmd}")
        cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
    else:  # Windows
        with open(log_file_path, 'r', encoding='utf-8') as file:
            cmd_result = file.readlines()[-num_of_lines:]
    return '\n'.join(cmd_result)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Admin Menu"))
@loggers.async_log_access
@bot_auth.super_admin_only
async def show_admin_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    fallback = (
        "➖➖**Admin Menu**➖➖\n"
        "‣ Commands:\n"
        " `/cmd logs` or `/cmd logs [search_string]`"
    )
    try:
        rich_card = keyboards.get_rich_admin_menu()
        await client.send_rich_message(chat_id, rich_card, reply_markup=keyboards.admin_menu_keyboard)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected rich admin menu; sending plain text")
        await utils.edit_and_send_msg(query, fallback, keyboards.admin_menu_keyboard)


# --------------------------------------------------
# Helper: replace Telegram IDs with names using DynamoDB
def _id_to_name(telegram_id: str, cache: dict) -> str:
    NO_LOOKUP = "UNKNOWN"
    if telegram_id in cache:
        return cache[telegram_id]
    try:
        resp = db.get_user_by_telegram_id(str(telegram_id))
        items = resp.get('Items', [])
        name = items[0].get('Name') if items else NO_LOOKUP
    except Exception as e:
        logger.error(f"DDB lookup failed for {telegram_id}: {e}")
        name = NO_LOOKUP
    cache[telegram_id] = name
    return name


# --------------------------------------------------
def _replace_ids_with_names(cmd_result: str) -> str:
    cache = {}
    lines = []
    for line in cmd_result.strip().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            count, telegram_id = parts[0], parts[1]
            name = _id_to_name(telegram_id, cache)
            lines.append(f"{count} {name}")
        else:
            lines.append(line)
    return "\n".join(lines)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Show Stats"))
@loggers.async_log_access
@bot_auth.super_admin_only
async def show_stats(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id

    date_string = datetime.now().strftime("%Y-%m-")
    month_name = datetime.now().strftime("%B %Y")
    log_file_path = os.path.join('/home', STOSCBOT_APP_HOME_DIR, 'bots', 'stoscbot', 'logs', 'stosc_logs.log')

    if platform.system() == "Linux":
        # Build pipeline: filter current-month logs, extract Telegram IDs from `[ID:...]`, count occurrences, sort desc, and take top 15.
        cmd = rf"""
        grep -E '{date_string}' {log_file_path} |
        grep -oP '(?<=\[)\d+(?=:)' |
        sort |
        uniq -c |
        sort -nr |
        head -n 15
        """
        cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        # Replace Telegram IDs with names from DynamoDB
        cmd_result = _replace_ids_with_names(cmd_result)

        fallback = f"** Top users by messages ({month_name}) **\n`{cmd_result}`"
        try:
            rich_card = keyboards.get_rich_admin_stats(month_name, cmd_result, host_supported=True)
            await client.send_rich_message(chat_id, rich_card, reply_markup=keyboards.admin_menu_keyboard)
        except RichMessageUnsupported:
            logger.warning("Telegram rejected rich admin stats; sending plain text")
            await utils.edit_and_send_msg(query, fallback, keyboards.admin_menu_keyboard)
    else:
        fallback = "This action is only available when the bot runs on Linux."
        try:
            rich_card = keyboards.get_rich_admin_stats(month_name, "", host_supported=False)
            await client.send_rich_message(chat_id, rich_card, reply_markup=keyboards.admin_menu_keyboard)
        except RichMessageUnsupported:
            await query.message.reply_text(fallback, reply_markup=keyboards.admin_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Show Logs"))
@loggers.async_log_access
@bot_auth.super_admin_only
async def show_logs(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id

    if platform.system() == "Linux":
        date_string = datetime.now().strftime("%Y-%m-")
        cmd = rf"grep -E '{date_string}' /home/{STOSCBOT_APP_HOME_DIR}/bots/stoscbot/logs/stosc_logs.log | grep -P '\[\d+:[^:]+:[^:\]]+\]' | grep -v '\[{VIBIN_TELEGRAM_ID}:vibinjk:Vibin\]' | tail -n 20"
        cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        fallback = f"** Last few log messages (current month) **\n`{cmd_result}`"
        try:
            rich_card = keyboards.get_rich_admin_logs("Recent System Activity 📜", cmd_result, is_error=False)
            await client.send_rich_message(chat_id, rich_card, reply_markup=keyboards.admin_menu_keyboard)
        except RichMessageUnsupported:
            await utils.edit_and_send_msg(query, fallback, keyboards.admin_menu_keyboard)
    else:
        await query.message.reply_text("This action is only available when the bot runs on Linux.", reply_markup=keyboards.admin_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Show Error Logs"))
@loggers.async_log_access
@bot_auth.super_admin_only
async def show_error_logs(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id

    if platform.system() == "Linux":
        date_string = datetime.now().strftime("%Y-")
        cmd = rf"grep -E '{date_string}' /home/{STOSCBOT_APP_HOME_DIR}/bots/stoscbot/logs/stosc_logs.log | grep -iE 'error|exception' | grep -v 'Telegram server could not fetch the provided URL' | grep -v '\[{VIBIN_TELEGRAM_ID}:vibinjk:Vibin\]' | tail -n 30"
        cmd_result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        fallback = f"** Last few error logs **\n`{cmd_result}`"
        try:
            rich_card = keyboards.get_rich_admin_logs("System Error Diagnostics ⚠️", cmd_result, is_error=True)
            await client.send_rich_message(chat_id, rich_card, reply_markup=keyboards.admin_menu_keyboard)
        except RichMessageUnsupported:
            await utils.edit_and_send_msg(query, fallback, keyboards.admin_menu_keyboard)
    else:
        await query.message.reply_text("This action is only available when the bot runs on Linux.", reply_markup=keyboards.admin_menu_keyboard)
