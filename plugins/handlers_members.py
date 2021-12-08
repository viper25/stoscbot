from pyrogram import Client, filters
from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils

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
@Client.on_callback_query(dynamic_data_filter("Member Birthday Today Button"))
@loggers.log_access
def get_today_bdays(client, query):
    query.answer()
    start, end, result=db.get_bday('d')
    if len(result) ==0:
        msg="No Birthdays today"
    elif len(result) > 0:
        msg="**Birthdays today** 🎂\n\n"
        for _item in result:
            msg += f"• {_item[1].strip()} `({_item[0].strip()})`\n"
    utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Member Anniversary Today Button"))
@loggers.log_access
def get_today_anniversaries(client, query):
    query.answer()
    start, end, result=db.get_anniversaries('d')
    if len(result) ==0:
        msg="No Wedding Anniversary today"
    else:
        msg="**Wedding Anniversarys today** 💍\n\n"
        for _item in result:
            msg += f"• {_item[1].strip()} `({_item[0].strip()})`\n"
    utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Member Birthday Week Button"))
@loggers.log_access
def get_weeks_bdays(client, query):
    query.answer()
    start, end, result=db.get_bday('w')
    if len(result) ==0:
        msg=" No Birthdays this week"
    else:
        msg="**Birthdays this week** 🎂\n"
        msg += f"`({start} - {end})`\n\n"
        for _item in result:
            msg += f"• {_item[1].strip()} `({_item[0].strip()})`\n"
    utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Member Anniversary Week Button"))
@loggers.log_access
def get_weeks_anniversaries(client, query):
    query.answer()
    start, end, result=db.get_anniversaries('w')
    if len(result) ==0:
        msg=" No Wedding Anniversaries this week"
    else:
        msg="**Wedding Anniversary** 💍\n"
        msg += f"`({start} - {end})`\n\n"
        for _item in result:
            msg += f"• {_item[1].strip()} `({_item[0].strip()})`\n"
    utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("GB Ineligible"))
@loggers.log_access
def member_gb_ineligible(client, query):
    query.answer()
    result=db.get_gb_ineligible()
    msg = f"**GB Ineligible** `({len(result)})`\n"
    msg += "➖➖➖➖➖➖\n"
    for member in result:
        msg += f"• {member[0].strip()} `({member[1]})`\n"
    utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)