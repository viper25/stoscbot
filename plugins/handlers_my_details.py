from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils
from datetime import datetime

# To display accounts that can be paid to. This MUST match the names as they appear in DDB as entered by the Xero job 'member_contribution.py'   
# Excluding 'Diocesan Development Fund' since that's an ad-hoc payment account
LIST_ACCOUNTS = ['Thanksgiving Auction','Thanksgiving Donation','Catholicate Fund','Metropolitan Fund','Seminary Fund','Resisa Donation','Marriage Assistance Fund','Mission Fund','Sunday School','Self Denial Fund','Birthday Offering','Baptism and Wedding Offering','Christmas Offering','Donations & Gifts','Holy Qurbana','Holy Week Donation','Member Subscription','Offertory','Tithe','Youth Fellowship']

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
    _member_code=utils.getMemberCode_from_TelegramID(query.from_user.id)
    result=db.get_member_details(_member_code,'code')
    msg = utils.generate_profile_msg(result)
    _booking_url = f"https://crm.stosc.com/stosc-forms/?id={db.get_booking_GUID(_member_code)[0][0]}"
    msg += f"• [Service Booking URL]({_booking_url})"
    msg += "\n\n`Please contact the church office to update any details`"
    await utils.send_profile_address_and_pic(client, query, msg,result, keyboards.my_details_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("My Contributions"))
@loggers.async_log_access
async def show_my_contributions(client: Client, query: CallbackQuery):
    await query.answer()
    # Set to current year
    _year=str(datetime.now().year)
    _member_code=utils.getMemberCode_from_TelegramID(query.from_user.id)
    result=db.get_member_details(_member_code, 'code')
    msg = utils.generate_msg_xero_member_payments(result[0][1], _member_code, _year)
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("My Subscriptions"))
@loggers.async_log_access
async def show_my_subscriptions(client: Client, query: CallbackQuery):
    await query.answer()
    # Set to current year
    _year=str(datetime.now().year)
    _member_code=utils.getMemberCode_from_TelegramID(query.from_user.id)
    msg = utils.generate_msg_xero_member_invoices(_member_code, _year)
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Help"))
@loggers.async_log_access
async def show_help(client: Client, query: CallbackQuery):
    await query.answer()
    msg="How to use\n"
    msg += "➖➖➖➖➖\n"
    msg += "• Click **Payments** button to access payments for current year\n"
    msg += "• Click **Subscription Invoices** button to access your subscription invoices for the current year\n"
    msg += "• Click **List of Accounts** button to see all accounts you may wish to contribute to\n"
    # msg += "• To see *m*ember *p*ayments for year 2020, type `'/mp 2020'` for payments for year 2020\nDo note, the new accounting system has only data from Oct 2020 onwards.\n"
    # msg += "• To see *m*ember *s*ubscription for year 2020, type `'/ms 2020'` for subscription payments for year 2020\n"
    msg += "`\nNote: Data available only from Oct 2020 onwards`\n"
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("List of Accounts"))
@loggers.async_log_access
async def show_list_accounts(client: Client, query: CallbackQuery):
    await query.answer()
    payments = utils.get_member_payments(utils.getMemberCode_from_TelegramID(query.from_user.id), str(datetime.now().year))
    msg="List of Accounts\n"
    msg += "➖➖➖➖➖➖\n"
    msg += "You may contribute towards the following accounts:\n"
    for account in LIST_ACCOUNTS:
        if any(payment.get('Account', '').startswith(account) for payment in payments):
            msg += f"• **{account}**\n"
        else:
            msg += f"• {account}\n"
    msg += "\n`*` **Bold** `indicates that you have contributed towards this account head`"
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)

