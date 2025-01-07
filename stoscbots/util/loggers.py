import datetime
import hashlib
import logging
import os
from functools import wraps
from logging.handlers import RotatingFileHandler

import boto3
import botocore.exceptions
from dotenv import load_dotenv

# Load environment variables from .env file (for the whole project)
# This here is one of the first entry points
load_dotenv()

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
ENV = os.environ.get("ENV").upper()

# Configuration
def get_config(key, default=None):
    return os.environ.get(key, default)


# Logger Initialization
def logger_init():
    logger = logging.getLogger()  # root logger

    # File handler
    log_path = get_config("STOSC_LOGS")
    rf_handler = RotatingFileHandler(log_path, maxBytes=1000000, backupCount=5, encoding='utf-8')
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    rf_handler.setFormatter(formatter)
    rf_handler.setLevel(LOGLEVEL)

    # Stream handler
    stream = logging.StreamHandler()
    streamformat = logging.Formatter("%(asctime)s [%(levelname)s]: %(name)s: %(message)s")
    stream.setLevel(LOGLEVEL)
    stream.setFormatter(streamformat)

    # Adding handlers
    logger.addHandler(rf_handler)
    if ENV != "PRO":
        logger.addHandler(stream)


logger_init()  ## init root logger
logger = logging.getLogger(__name__)  ## module logger
logger.setLevel(LOGLEVEL)

resource = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ.get("STOSC_DDB_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("STOSC_DDB_SECRET_ACCESS_KEY"),
    region_name="ap-southeast-1",
)
table_stosc_bot_member_telegram = resource.Table("stosc_bot_member_telegram")

# Update metrics only if using PRO STOSC Bot Token
log_metrics = hashlib.md5(
    os.environ.get("STOSC_TELEGRAM_BOT_TOKEN").encode()).hexdigest() == "defd1d2832a12584e5b5611da9a10fcc"


# Log Bot user access metrics
def handle_error(e, telegram_id):
    if isinstance(e, botocore.exceptions.ClientError) and e.response['Error']['Code'] == 'ValidationException':
        logger.warning(f"{telegram_id} is not a member, skipping update of access metrics")
    else:
        logger.error(f"{telegram_id} update failed with error: {e}", exc_info=True)


def update_access_metrics(telegram_id):
    '''
    If this is a non-member, i.e. a random user who stumbled by this bot, the insert will fail on account of there being no record to
    update and we capture the exception and move along
    '''
    try:
        table_stosc_bot_member_telegram.update_item(
            Key={'telegram_id': str(telegram_id)},
            UpdateExpression="SET hits = hits + :inc, last_seen = :modified_ts_val",
            ExpressionAttributeValues={
                ':inc': 1,
                ":modified_ts_val": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            }
        )
    except Exception as e:
        handle_error(e, telegram_id)


# Log Bot user access metrics. This is to be decorated ONLY on async functions
def async_log_access(func):
    @wraps(func)
    # See: https://stackoverflow.com/questions/44169998/how-to-create-a-python-decorator-that-can-wrap-either-coroutine-or-function#comment111746175_63156433
    async def function_wrapper(*args, **kwargs):
        if log_metrics:
            update_access_metrics(args[1].from_user.id)
        arg_msg = ""
        if hasattr(args[1], 'text') and args[1].text:
            # For Commands not buttons
            arg_msg = f" with text: '{args[1].text}'"
            # arg_msg=f" with args={args[1].command[0]}"
        elif hasattr(args[1], 'data') and args[1].data:
            # The Callback text for the Button
            arg_msg = f" for button: '{args[1].data}'"

        logger.info(
            f"{func.__module__}.{func.__name__} called by [{args[1].from_user.id}:{args[1].from_user.username}:{args[1].from_user.first_name}]" + arg_msg)
        # If the wrapped function is an aysnc function, we need to await it
        return await func(*args, **kwargs)

    return function_wrapper
