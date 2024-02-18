import logging
from datetime import datetime

from pyrogram import Client, filters
from pyrogram import enums
from pyrogram.types import Message, CallbackQuery

from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from stoscbots.util.utils import format_telegram_message
from stoscbots.xero import xero_utils

# ==================================================

# Module logger
logger = logging.getLogger('Handler.Finance')
logger.setLevel(loggers.LOGLEVEL)

# --------------------------------------------------

'''
Handle multiple callback queries data and return filter for each
'''


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data  # "data" kwarg is accessed with "flt.data" above
    )


def dynamic_data_filter_starts_with(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data),
        data=data  # "data" kwarg is accessed with "flt.data" above
    )


async def get_member_code_and_year(message: Message):
    """
    Utility function to get member code and year from message command
    """
    if len(message.command) < 2 or not utils.is_valid_member_code(message.command[1].upper()):
        await message.reply("Please enter a valid Member Code to search", quote=True)
        return None, None

    member_code = message.command[1].upper()
    year = message.command[2] if len(message.command) == 3 else str(datetime.now().year)
    return member_code, year


# --------------------------------------------------
@Client.on_message(filters.command(["x", "xs"]))
@loggers.async_log_access
@bot_auth.async_management_only
async def finance_search_member(client: Client, message: Message):
    member_code, year = await get_member_code_and_year(message)
    if not member_code:
        return

    result = db.get_member_details(member_code, 'code')
    if not result:
        await message.reply("No such Member")
        return

    if message.command[0] == "x":
        msg = utils.generate_msg_xero_member_payments(result[0][2], member_code, year)
    elif message.command[0] == "xs":
        msg = utils.generate_msg_xero_member_invoices(member_code, year)

    await message.reply(msg)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Executive Summary Button"))
@loggers.async_log_access
async def get_finance_executive_summary(client: Client, query: CallbackQuery):
    await query.answer()
    report = xero_utils.get_executive_summary()['Reports'][0]['Rows']
    variance_symbols = {"-": "▼", "": "▲"}

    def format_value(value):
        return f"{value if ('%' in value or value == '') else round(float(value), 1):,.2f}"

    filtered_rows = [row for row in report if
                     row.get('Title', '').upper() not in ['POSITION', 'PERFORMANCE', 'PROFITABILITY', 'INCOME']]

    msg_parts = ["➖**EXECUTIVE SUMMARY**➖\n\n"]
    for row in filtered_rows:
        if row['RowType'] == 'Header':
            current_month_title = row['Cells'][1]['Value']
            previous_month_title = row['Cells'][2]['Value']
        else:
            logger.debug(f"In Section: {row['Title']}")
            msg_parts.append(f"**==========\n📌SECTION: {row['Title'].upper()}**\n")
            for section in row['Rows']:
                logger.debug(f"get_finance_executive_summary: Processing [{section['Cells'][0]['Value']}]")
                msg_parts.extend([
                    "〰〰〰〰〰\n",
                    f"**{section['Cells'][0]['Value']}**\n",
                    f"{previous_month_title}={format_value(section['Cells'][2]['Value'])}\n",
                    f"{current_month_title}={format_value(section['Cells'][1]['Value'])}\n",
                    f"Variance={variance_symbols.get(section['Cells'][3]['Value'][:1], '▲')}{section['Cells'][3]['Value']}\n"
                ])

    msg = ''.join(msg_parts)
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Bank Summary Button"))
@loggers.async_log_access
async def get_finance_bank_summary(client: Client, query: CallbackQuery):
    await query.answer()
    report = xero_utils.get_bank_summary()['Reports'][0]['Rows']

    def format_bank_account_data(bank_account_data):
        closing_bal_value = bank_account_data['Cells'][4]['Value'] or '0'
        return f"""
        〰〰〰〰〰
        **{bank_account_data['Cells'][0]['Value']}**
        {header['Cells'][1]['Value']}=${float(bank_account_data['Cells'][1]['Value'] or '0'):,.2f}
        {header['Cells'][2]['Value']}=${float(bank_account_data['Cells'][2]['Value'] or '0'):,.2f}
        {header['Cells'][3]['Value']}=${float(bank_account_data['Cells'][3]['Value'] or '0'):,.2f}
        **{header['Cells'][4]['Value']}=${float(closing_bal_value):,.2f}**
        """

    msg_parts = ["➖**BANK ACCOUNTS SUMMARY**➖\n\n"]
    all_fd_sum = 0.0

    for row in report:
        if row['RowType'] == 'Header':
            header = row
        else:
            for bank_account_data in row['Rows']:
                bank_account = bank_account_data['Cells'][0]['Value']
                logger.debug(f"Processing [{bank_account}]")

                closing_bal_value = bank_account_data['Cells'][4]['Value'] or '0'

                if bank_account.startswith('DBS FD'):
                    all_fd_sum += float(closing_bal_value)
                    continue

                if float(closing_bal_value) != 0:
                    msg_parts.append(format_bank_account_data(bank_account_data))

    msg_parts.append("--------------------\n")
    msg_parts.append(f"(Fixed Deposits=**${float(all_fd_sum):,.2f}**)\n")

    msg = ''.join(msg_parts)

    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter_starts_with("Finance Trial Balance"))
@loggers.async_log_access
async def get_finance_trial_balance(client: Client, query: CallbackQuery):
    await query.answer()
    is_income_report = "REVENUE" in query.data.upper()

    def __get_msg(rows, report_type):
        value_index = {'revenue': 4, 'expense': 3}
        __msg = "\n".join(
            f"{row['Cells'][0]['Value']}\n**${float(row['Cells'][value_index[report_type]]['Value'] or 0):,.2f}**\n––––————————————————"
            for row in rows
        )
        logger.debug(f"get_finance_trial_balance: Processed {len(rows)} rows.")
        return __msg

    report = xero_utils.xero_get_trial_balance(_paymentsOnly=is_income_report)['Reports'][0]['Rows']
    report_type = 'revenue' if is_income_report else 'expense'
    msg_rows = __get_msg(report[1 if is_income_report else 2]['Rows'], report_type)

    msg = f"**TRIAL BALANCE**\n`For Year {datetime.now().year}`\n➖➖➖➖➖➖➖\n\n{msg_rows}"
    msg = format_telegram_message(msg)
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Payments WTD Button"))
@loggers.async_log_access
async def get_finance_payments_wtd_balance(client: Client, query: CallbackQuery):
    await query.answer()
    payments = xero_utils.xero_get_payments()

    msg_list = ["➖**INVOICE/BILL PAYMENTS**➖\n\n"]

    for payment in payments.get('Payments', []):
        if payment['Status'] == 'DELETED':
            continue

        inv_type_icon = '⇨' if payment['Invoice']['Type'] == 'ACCPAY' else '⇦' if payment['Invoice'][
                                                                                      'Type'] == 'ACCREC' else ''
        icon = '🔴' if payment['Invoice']['Type'] == 'ACCPAY' else '🟢' if payment['Invoice']['Type'] == 'ACCREC' else ''
        _date = xero_utils.parse_Xero_Date(payment['Date'])
        contact_name = payment['Invoice']['Contact']['Name']
        invoice_number = payment['Invoice'].get('InvoiceNumber', '-NA-')
        if invoice_number == '':
            invoice_number = '-NA-'
        amount = payment['Amount']

        msg_list.append(f"\n{icon} **{contact_name}** ({invoice_number})\n")
        msg_list.append(f"`({_date:%Y-%m-%d})` ")
        msg_list.append(f"**${amount}** {inv_type_icon}\n")

    msg = ''.join(msg_list)
    msg = format_telegram_message(msg)

    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)


# --------------------------------------------------

@Client.on_callback_query(dynamic_data_filter("Finance Latest Transactions Button"))
@loggers.async_log_access
async def get_finance_latest_tx(client: Client, query: CallbackQuery):
    await query.answer()
    bank_tx = xero_utils.xero_get_bank_transactions()
    now = datetime.now()
    msg_parts = ["➖**TRANSACTIONS (WTD)**➖\n`No Invoice (subscription) or bill payment transactions shown`\n\n"]

    for tx in bank_tx['BankTransactions']:
        tx_date = xero_utils.parse_Xero_Date(tx['Date'])
        if tx_date > now:
            continue

        icon = '❓'
        _msg = ''
        tx_type = tx['Type']
        if tx_type == 'RECEIVE':
            icon = '🟢'
        elif tx_type in {'SPEND', 'SPEND-TRANSFER'}:
            icon = '🔴'
            if tx_type == 'SPEND-TRANSFER':
                _msg = " `(Transfer Out)`"
        elif tx_type == 'RECEIVE-TRANSFER':
            icon = '🟢'
            _msg = " `(Transfer In)`"

        if 'Contact' in tx:
            msg_parts.append(f"{icon} **{tx['Contact']['Name']}** ")

        bank_account_name = tx['BankAccount']['Name'].upper()
        if bank_account_name == 'CASH':
            msg_parts.append(f"💵 CASH {_msg}\n")
        elif 'DBS' in bank_account_name:
            msg_parts.append(f"🏦 DBS {_msg}\n")
        elif bank_account_name == 'NETS':
            msg_parts.append(f"💳 NETS {_msg}\n")
        else:
            msg_parts.append(f"\n\n{icon} **{tx['BankAccount']['Name']}** {_msg}\n")

        msg_parts.append(f"`{tx_date:%Y-%m-%d}`\n")
        msg_parts.append(f"**${tx['Total']}**\n\n")

    msg = ''.join(msg_parts)
    msg = format_telegram_message(msg)
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Projects Button"))
@loggers.async_log_access
async def get_finance_tracking(client: Client, query: CallbackQuery):
    await query.answer()
    msg = utils.get_tracked_projects()
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Outstanding Button"))
@loggers.async_log_access
async def get_finance_outstandings(client: Client, query: CallbackQuery):
    await query.answer()
    msg = utils.get_outstandings()
    client.set_parse_mode(enums.ParseMode.MARKDOWN)
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)
