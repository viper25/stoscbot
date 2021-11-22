from functools import wraps
import logging
import boto3
import datetime
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger=logging.getLogger(__name__)

resource=boto3.resource('dynamodb', aws_access_key_id=os.environ.get('STOSC_DDB_ACCESS_KEY_ID'), aws_secret_access_key=os.environ.get('STOSC_DDB_SECRET_ACCESS_KEY'), region_name='ap-southeast-1')
table_telegram_members=resource.Table('stosc_bot_member_telegram')

# Log Bot user access metrics
def update_access_metrics(telegram_id):
    try:
        table_telegram_members.update_item(
            Key = {'telegram_id': str(telegram_id)},
            UpdateExpression = "SET hits = if_not_exists(hits, :start) + :inc, last_seen = :modified_ts_val",
            ExpressionAttributeValues = {
                ':inc': 1,
                ':start': 0,
                ":modified_ts_val": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") 
            }
        )
    except Exception as e:
        logger.error(e)


def log_access(func):
    @wraps(func)
    def function_wrapper(*args, **kwargs):
        update_access_metrics(args[1].from_user.id)
        arg_msg=""
        if hasattr(args[1], 'text') and args[1].text:
            # For Commands not buttons
            arg_msg=f" with text: '{args[1].text}'"
            # arg_msg=f" with args={args[1].command[0]}"
        elif hasattr(args[1], 'data') and args[1].data:
            # The Callback text for the Button
            arg_msg=f" for button: '{args[1].data}'"

        logger.info(f"{func.__module__}.{func.__name__} called by [{args[1].from_user.id}:{args[1].from_user.username}:{args[1].from_user.first_name}]" + arg_msg)
        # Call the original passed-in function
        return func(*args, **kwargs)
    return function_wrapper

def info(e):
    logger.info(e)

def error(e):
    logger.error(e)

def warn(e):
    logger.warn(e)

def debug(e):
    logger.debug(e)