from pyrogram import Client, filters
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from stoscbots.bot import keyboards
from stoscbots.xero import xero_utils
from datetime import datetime
# ==================================================
'''
Handle multiple callback queries data and return filter for each
'''
def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data  # "data" kwarg is accessed with "flt.data" above
    )
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("St. Marys Project Summary Button"))
@loggers.log_access
def get_finance_stmarys_executive_summary(client, query):
    query.answer()
    msg = "**EXECUTIVE SUMMARY\n"
    msg += "➖➖➖➖➖➖➖➖➖\n\n"
    report = utils.get_tracked_projects(raw_data=True)
    for _item in report:
        if _item['AccountName'] == 'Snehasparsham':
            msg += f"• **{_item['AccountName']}** - `${_item['Total']:,.2f}`\n"
        elif _item['AccountName'] == 'Vanitha Dinam':
            msg += f"• **{_item['AccountName']}** - `${_item['Total']:,.2f}`\n"
        elif _item['AccountName'] == 'Pethrutha':
            msg += f"• **{_item['AccountName']}** - `${_item['Total']:,.2f}`\n"
    utils.edit_and_send_msg(query, msg, keyboards.stmarys_menu_keyboard)
