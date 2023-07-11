from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils
from datetime import datetime

# To display accounts that can be paid to. This MUST match the names as they appear in DDB as entered by the Xero job 'member_contribution.py'   
# Excluding 'Diocesan Development Fund' since that's an ad-hoc payment account
LIST_ACCOUNTS = ['Thanksgiving Auction', 'Thanksgiving Donation', 'Catholicate Fund', 'Metropolitan Fund',
                 'Seminary Fund', 'Resisa Donation', 'Marriage Assistance Fund', 'Mission Fund', 'Sunday School',
                 'Self Denial Fund', 'Birthday Offering', 'Baptism and Wedding Offering', 'Christmas Offering',
                 'Donations & Gifts', 'Holy Qurbana', 'Holy Week Donation', 'Kohne Sunday', 'Member Subscription',
                 'Offertory', 'Tithe', 'Youth Fellowship']

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
    msg = utils.generate_msg_xero_member_payments(result[0][1], _member_code, _year)
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
    msg = "**List of Accounts**\n"
    msg += "➖➖➖➖➖➖\n"
    msg += "You may contribute towards the following accounts:\n"
    for account in LIST_ACCOUNTS:
        payment_account_head_added = False
        for payment in payments:
            if payment.get('Account', '').startswith(account):
                msg += f"• **{account} `(${payment['LineAmount']:,.2f})`**\n"
                payment_account_head_added = True  # To avoid duplicate lines being printed
        if not payment_account_head_added:
            msg += f"• {account}\n"
            payment_account_head_added = False
    msg += "\n`*` **Bold** `indicates that you have contributed towards this account head`"
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)
