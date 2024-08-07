import logging
import os
from functools import wraps

import boto3
from boto3.dynamodb.conditions import Key

from stoscbots.util.loggers import LOGLEVEL

# =================================================

# Module logger
logger = logging.getLogger('Handler.Both_Auth')
logger.setLevel(LOGLEVEL)
# =================================================

ACCESS_DENIED_TEXT = "⛔️**RESTRICTED ACCESS**⛔️"
ACCESS_DENIED_MEMBERS_TEXT = "⛔️**ACCESS DENIED**⛔️\n➖➖➖➖➖➖➖➖\n If you wish to access the bot and see your contribution statements, contact the [Lay Steward](https://t.me/stosc_accounts) or email accounts@stosc.com for access."

VIBIN_TELEGRAM_ID = os.environ.get('VIBIN_TELEGRAM_ID')

resource = boto3.resource('dynamodb', aws_access_key_id=os.environ.get('STOSC_DDB_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.environ.get('STOSC_DDB_SECRET_ACCESS_KEY'),
                          region_name='ap-southeast-1')
table_stosc_bot_member_telegram = resource.Table('stosc_bot_member_telegram')


def get_super_admin_ids():
    return os.environ.get('SUPER_ADMIN_TELEGRAM_IDS', '')


async def send_access_denied_msg(client, msg_or_query):
    arg_msg = ""
    if hasattr(msg_or_query, 'text') and msg_or_query.text:
        # For Commands not buttons
        await msg_or_query.reply_sticker(
            sticker='CAACAgIAAxkBAAIFJV-X6UKaAAEDx4Nqup6acSBW6DlThgACoAMAAvoLtgj5yjtMiAXK4hsE')
        await msg_or_query.reply_text(text=ACCESS_DENIED_MEMBERS_TEXT, quote=True, disable_web_page_preview=True)
        arg_msg = f"'{msg_or_query.text}'"
        # arg_msg=f" with args={message.command[0]}"
        logger.warning(
            f"Unauthorized Access by [{msg_or_query.from_user.id}:{msg_or_query.from_user.username}:{msg_or_query.from_user.first_name}]. Command sent: {arg_msg}")
    elif hasattr(msg_or_query, 'data') and msg_or_query.data:
        # Button callback
        await msg_or_query.answer()
        await client.send_sticker(chat_id=msg_or_query.from_user.id,
                                  sticker='CAACAgIAAxkBAAIFJV-X6UKaAAEDx4Nqup6acSBW6DlThgACoAMAAvoLtgj5yjtMiAXK4hsE')
        await client.send_message(chat_id=msg_or_query.from_user.id, text=ACCESS_DENIED_MEMBERS_TEXT,
                                  disable_web_page_preview=True)
        # The Callback text for the Button
        arg_msg = f"'{msg_or_query.data}'"
        logger.warning(
            f"Unauthorized Access by [{msg_or_query.from_user.id}:{msg_or_query.from_user.username}:{msg_or_query.from_user.first_name}]. Button clicked: {arg_msg}")

    # Notify superadmin on Unauthorized access
    unauth_msg = f"Unauthorized Access by **[{msg_or_query.from_user.id}:{msg_or_query.from_user.username}:{msg_or_query.from_user.first_name}]**\nCmd/Button: `{arg_msg}`"
    await client.send_message(chat_id=get_super_admin_id(), text=unauth_msg)


# =================================================
# To decorate functions that serves /u and /x commands
def async_member_only(func):
    # Can see ALL the buttons
    @wraps(func)
    # If used for other functions with diff signature, change parameters to *args, **kwargs
    # Msg for commands such as /start and Query for Button callbacks
    async def wrapped(client, msg_or_query):
        if not is_member(msg_or_query.from_user.id):
            await send_access_denied_msg(client, msg_or_query)
            return
        return await func(client, msg_or_query)

    return wrapped


# =================================================
# To decorate functions that serves /u and /x commands
def async_management_only(func):
    # Can see ALL the buttons
    @wraps(func)
    # If used for other functions with diff signature, change parameters to *args, **kwargs
    # Msg for commands such as /start and Query for Button callbacks
    async def wrapped(client, msg_or_query):
        if not is_mgmt_member(msg_or_query.from_user.id):
            await send_access_denied_msg(client, msg_or_query)
            return
        return await func(client, msg_or_query)

    return wrapped


# --------------------------------------------------
def async_area_prayer_coordinator_only(func):
    # Can see ALL the buttons
    @wraps(func)
    # If used for other functions with diff signature, change parameters to *args, **kwargs
    # Msg for commands such as /start and Query for Button callbacks
    async def wrapped(client, msg_or_query):
        if not (is_area_prayer_coordinator_member(msg_or_query.from_user.id) or is_mgmt_member(
                msg_or_query.from_user.id)):
            await send_access_denied_msg(client, msg_or_query)
            return
        return await func(client, msg_or_query)

    return wrapped


# --------------------------------------------------
# Decorator for super admin check
def super_admin_only(func):
    wraps(func)

    async def wrapper(client, message):
        if not is_super_admin(message.from_user.id):
            await message.reply_text("You are not allowed to execute this command")
            return
        return await func(client, message)

    return wrapper


# =================================================
def is_member(telegram_id: int) -> bool:
    response = table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        return True


# --------------------------------------------------
def is_mgmt_member(telegram_id: int) -> bool:
    response = table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        if 'auth' in response['Items'][0] and 'mc' in response['Items'][0]['auth']:
            return True


# --------------------------------------------------
def is_area_prayer_coordinator_member(telegram_id: int) -> bool:
    response = table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        if 'auth' in response['Items'][0] and (
                'apc' in response['Items'][0]['auth'] or 'mc' in response['Items'][0]['auth']):
            return True


def get_super_admin_id():
    return VIBIN_TELEGRAM_ID


def is_super_admin(telegram_id: int) -> bool:
    super_admin_ids_list = get_super_admin_ids().split(',')
    super_admin_ids = [int(id_str) for id_str in super_admin_ids_list if id_str.isdigit()]
    if telegram_id in super_admin_ids:
        return True
    else:
        return False
