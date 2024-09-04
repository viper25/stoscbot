from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils
from datetime import datetime
from stoscbots.xero import xero_utils

LIST_ACCOUNTS = xero_utils.get_chart_of_accounts(class_type='REVENUE')
LIST_ACCOUNTS = [x for x in LIST_ACCOUNTS if x['Code'] != '3230']   # Interest Income
LIST_ACCOUNTS = [x for x in LIST_ACCOUNTS if x['Code'] != '3231']   # Fixed Deposit Interest

# ==================================================
'''
Handle multiple callback queries data and return filter for each
'''


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data  # "data" kwarg is accessed with "flt.data" above
    )


# ==================================================
# Callback Handlers (for Buttons)
@Client.on_callback_query(dynamic_data_filter("My Profile"))
@loggers.async_log_access
async def show_my_profile(client: Client, query: CallbackQuery):
    await query.answer()
    _member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    result = db.get_member_details(_member_code, 'code')
    msg = utils.generate_profile_msg_for_family(result)
    # Service booking disabled for now
    # _booking_url = f"https://crm.stosc.com/stosc-forms/?id={db.get_booking_GUID(_member_code)[0][0]}"
    # msg += f"• [Service Booking URL]({_booking_url})"
    msg += "\n`Please contact the church office or secretary@stscoc.com to update any details. Type /help to see Help`"
    await utils.send_profile_address_and_pic(client, query, msg, result, searched_person=None,
                                             searched_person_name=None, keyboard=keyboards.my_details_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("My Contributions"))
@loggers.async_log_access
async def show_my_contributions(client: Client, query: CallbackQuery):
    await query.answer()
    # Set to current year
    _year = str(datetime.now().year)
    _member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    result = db.get_member_details(_member_code, 'code')
    msg = utils.generate_msg_xero_member_payments(f"{result[0][2]} `({result[0][1]})`", _member_code, _year)
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("My Dues"))
@loggers.async_log_access
async def show_my_subscriptions(client: Client, query: CallbackQuery):
    await query.answer()
    # Set to current year
    _year = str(datetime.now().year)
    _member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    msg = utils.generate_msg_xero_member_invoices(_member_code, _year)
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("List of Accounts"))
@loggers.async_log_access
async def show_list_accounts(client: Client, query: CallbackQuery):
    await query.answer()
    payments = utils.get_member_payments(utils.getMemberCode_from_TelegramID(query.from_user.id),
                                         str(datetime.now().year))
    msg = ">**List of Accounts**\n"
    msg += "➖➖➖➖➖➖\n"
    msg += "You may contribute towards the following accounts:\n\n"
    for account in LIST_ACCOUNTS:
        payment_account_head_added = False
        for payment in payments:
            if payment['AccountCode'].split('_')[1] == account['Code']:
                msg += f"• **{account['Name']} `(${payment['LineAmount']:,.0f})`**\n"
                payment_account_head_added = True  # To avoid duplicate lines being printed
        if not payment_account_head_added:
            msg += f"• {account['Name']}\n"
    msg += "\n__**Bold** indicates that you have contributed towards this account head__"
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)
