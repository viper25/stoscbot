from functools import wraps
from stoscbots.util import loggers
import os
import boto3
from boto3.dynamodb.conditions import Key

ACCESS_DENIED_TEXT = "⛔️**RESTRICTED ACCESS**⛔️"
ACCESS_DENIED_MEMBERS_TEXT = "⛔️**ACCESS DENIED**⛔️\n➖➖➖➖➖➖➖➖\n If you wish to see your contribution statements, contact [Lay Steward](https://t.me/stosc_accounts) or email accounts@stosc.com for access"
VIBIN_TELEGRAM_ID = 22541119

resource=boto3.resource('dynamodb', aws_access_key_id=os.environ.get('STOSC_DDB_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('STOSC_DDB_SECRET_ACCESS_KEY'), region_name='ap-southeast-1')
table_stosc_bot_member_telegram=resource.Table('stosc_bot_member_telegram')

def send_access_denied_msg(client, msg_or_query):

    arg_msg=""
    if hasattr(msg_or_query, 'text') and msg_or_query.text:
        # For Commands not buttons
        msg_or_query.reply_sticker(sticker='CAACAgIAAxkBAAIFJV-X6UKaAAEDx4Nqup6acSBW6DlThgACoAMAAvoLtgj5yjtMiAXK4hsE')
        msg_or_query.reply_text(text=ACCESS_DENIED_MEMBERS_TEXT,quote=True,disable_web_page_preview=True)
        arg_msg=f"'{msg_or_query.text}'"
        # arg_msg=f" with args={message.command[0]}"
        loggers.warn(f"Unauthorized Access by [{msg_or_query.from_user.id}:{msg_or_query.from_user.username}:{msg_or_query.from_user.first_name}]. Command sent: {arg_msg}")
    elif hasattr(msg_or_query, 'data') and msg_or_query.data:
        #Button callback
        msg_or_query.answer()
        client.send_sticker(chat_id=msg_or_query.from_user.id, sticker='CAACAgIAAxkBAAIFJV-X6UKaAAEDx4Nqup6acSBW6DlThgACoAMAAvoLtgj5yjtMiAXK4hsE')
        client.send_message(chat_id=msg_or_query.from_user.id, text=ACCESS_DENIED_MEMBERS_TEXT,disable_web_page_preview=True)
        # The Callback text for the Button
        arg_msg=f"'{msg_or_query.data}'"
        loggers.warn(f"Unauthorized Access by [{msg_or_query.from_user.id}:{msg_or_query.from_user.username}:{msg_or_query.from_user.first_name}]. Button clicked: {arg_msg}")

    # Notify Vibin on Unauthorized access
    unauth_msg=f"Unauthorized Access by **[{msg_or_query.from_user.id}:{msg_or_query.from_user.username}:{msg_or_query.from_user.first_name}]**\nCmd/Button: `{arg_msg}`"
    client.send_message(chat_id=VIBIN_TELEGRAM_ID,text=unauth_msg)

# =================================================
# To decorate functions that serves /u and /x commands
def management_only(func):
    # Can see ALL the buttons
    @wraps(func)
    # If used for other functions with diff signature, change parameters to *args, **kwargs
    # Msg for commands such as /start and Query for Button callbacks
    def wrapped(client, msg_or_query):
        if not is_mgmt_member(msg_or_query.from_user.id):
            send_access_denied_msg(client, msg_or_query)
            return
        return func(client, msg_or_query)
    return wrapped
# --------------------------------------------------
# To decorate functions for /u
def area_prayer_coordinator_only(func):
    # Can see ALL the buttons
    @wraps(func)
    # If used for other functions with diff signature, change parameters to *args, **kwargs
    # Msg for commands such as /start and Query for Button callbacks
    def wrapped(client, msg_or_query):
        if not (is_area_prayer_coordinator_member(msg_or_query.from_user.id) or is_mgmt_member(msg_or_query.from_user.id)):
            send_access_denied_msg(client, msg_or_query)
            return
        return func(client, msg_or_query)
    return wrapped
# =================================================
def is_mgmt_member(telegram_id):
    response=table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        if 'auth' in response['Items'][0] and 'mc' in response['Items'][0]['auth']:
            return True
    else:
        return False 
# --------------------------------------------------
def is_smo_member(telegram_id):
    response=table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        if 'auth' in response['Items'][0] and ('smo' in response['Items'][0]['auth'] or 'mc' in response['Items'][0]['auth']):
            return True
    else:
        return False 
# --------------------------------------------------
def is_area_prayer_coordinator_member(telegram_id):
    response=table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        if 'auth' in response['Items'][0] and ('apc' in response['Items'][0]['auth'] or 'mc' in response['Items'][0]['auth']):
            return True
    else:
        return False 