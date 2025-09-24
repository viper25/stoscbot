from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from stoscbots.bot import keyboards
from dateutil import parser
import gspread

"""
Handle multiple callback queries data and return filter for each
"""


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data), data=data  # "data" kwarg is accessed with "flt.data" above
    )
