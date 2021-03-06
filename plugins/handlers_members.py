from datetime import date
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
import math 
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
@loggers.async_log_access
async def get_today_bdays(client: Client, query: CallbackQuery):
    await query.answer()
    start, end, result=db.get_bday('d')
    if len(result) ==0:
        msg="No Birthdays today"
    elif len(result) > 0:
        msg="**Birthdays today** 🎂\n\n"
        for _item in result:
            _splits = _item[2].split('/')
            # Not all members provide year, therefore check if present
            if len(_splits) == 3:
                age =  date.today().year - int(_splits[2])
            else:
                age = None
            msg += f"• {_item[1].strip()} `({_item[0].strip()})` - {age if age else 'NA'}\n"
    await utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Member Anniversary Today Button"))
@loggers.async_log_access
async def get_today_anniversaries(client: Client, query: CallbackQuery):
    await query.answer()
    start, end, result=db.get_anniversaries('d')
    if len(result) ==0:
        msg="No Wedding Anniversary today"
    else:
        msg="**Wedding Anniversarys today** 💍\n\n"
        for _item in result:
            anniversary_years =  date.today().year - _item[2].year
            msg += f"• {_item[1].strip()} `({_item[0].strip()})` - {anniversary_years if anniversary_years else 'NA'}\n"
    await utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)
# --------------------------------------------------
@Client.on_message(filters.command(["bday"]))   # For when we want to print bdays without age
@Client.on_callback_query(dynamic_data_filter("Member Birthday Week Button"))
@loggers.async_log_access
async def get_weeks_bdays(client: Client, query_or_msg):
    dont_show_age = True
    if type(query_or_msg) == CallbackQuery:
        await query_or_msg.answer()
        dont_show_age = False
    start, end, result=db.get_bday('w')
    if len(result) ==0:
        msg=" No Birthdays this week"
    else:
        msg="**Birthdays this week** 🎂\n"
        msg += f"`({start} - {end})`\n\n"
        for _item in result:
            _splits = _item[2].split('/')
            _day = _splits[0].zfill(2)
            _month = _splits[1].zfill(2)
            # Not all members provide year, therefore check if present
            if len(_splits) == 3:
                age =  date.today().year - int(_splits[2])
            else:
                age = None
            if  _day == date.today().strftime("%d") and _month == date.today().strftime("%m") :
                if dont_show_age:
                    msg += f"•** {_item[1].strip()}** `({_item[0].strip()})`\n"
                else:
                    msg += f"•** {_item[1].strip()}** `({_item[0].strip()})` - **{age if age else 'NA'}**\n"
            else:
                if dont_show_age:
                    msg += f"• {_item[1].strip()} `({_item[0].strip()})`\n"
                else:
                    msg += f"• {_item[1].strip()} `({_item[0].strip()})` - {age if age else 'NA'}\n"
    if type(query_or_msg) == CallbackQuery:
        await utils.edit_and_send_msg(query_or_msg, msg, keyboards.members_menu_keyboard)
    else:
        await query_or_msg.reply_text(msg)
# --------------------------------------------------
@Client.on_message(filters.command(["anniv"]))   # For when we want to print bdays without age
@Client.on_callback_query(dynamic_data_filter("Member Anniversary Week Button"))
@loggers.async_log_access
async def get_weeks_anniversaries(client: Client, query_or_msg):
    dont_show_anniv_years = True
    if type(query_or_msg) == CallbackQuery:
        await query_or_msg.answer()
        dont_show_anniv_years = False
    start, end, result=db.get_anniversaries('w')
    if len(result) ==0:
        msg=" No Wedding Anniversaries this week"
    else:
        msg="**Wedding Anniversary** 💍\n"
        msg += f"`({start} - {end})`\n\n"
        for _item in result:
            anniversary_years = None
            if _item[2].year != 1900:
                anniversary_years =  str(date.today().year - _item[2].year) + ' yrs'
            if _item[2].day == date.today().day and _item[2].month == date.today().month:
                if dont_show_anniv_years:
                    msg += f"•** {_item[1].strip()}** `({_item[0].strip()})`\n"
                else:
                    msg += f"•** {_item[1].strip()}** `({_item[0].strip()})` - **{anniversary_years if anniversary_years else 'NA'}**\n"
            else:
                if dont_show_anniv_years:
                    msg += f"• {_item[1].strip()} `({_item[0].strip()})`\n"
                else:
                    msg += f"• {_item[1].strip()} `({_item[0].strip()})` - {anniversary_years if anniversary_years else 'NA'}\n"
    if type(query_or_msg) == CallbackQuery:
        await utils.edit_and_send_msg(query_or_msg, msg, keyboards.members_menu_keyboard)
    else:
        await query_or_msg.reply_text(msg)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("GB"))
@loggers.async_log_access
async def member_gb_ineligible(client: Client, query: CallbackQuery):
    await query.answer()
    result=db.get_gb_eligible_count()
    msg = f"**GB Eligible = ** `{result[0][0]}`\n"
    msg += f"**Quorum `(25%)` = ** `{math.floor(result[0][0]/4)}`\n"
    await utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)