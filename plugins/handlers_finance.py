from datetime import datetime
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from stoscbots.bot import keyboards
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
# --------------------------------------------------
@Client.on_message(filters.command(["x"]))
@loggers.async_log_access
@bot_auth.async_management_only
async def finance_search_member_payments(client: Client, message: Message):
    member_code = None
    if len(message.command) >= 2:
        member_code = message.command[1].upper()
        # There is atleast a member code sent
        # Match member codes such as V019. One char followed by 2 or 3 digits
        if utils.is_valid_member_code(member_code) is None:
            msg="Please enter a Member Code to search"
            await message.reply(msg,quote=True)
            return
    #A member code has been sent
    if member_code:
        result=db.get_member_details(member_code, 'code')
        if len(result) == 0:
            await message.reply("No such Member")
            return  
        elif len(result) >= 1:
            # Figure out the year of accounts we want to retrieve 
            # /x v019 2020
            if len(message.command) == 3:
                _year=message.command[2]
            # /x v019
            elif len(message.command) == 2:
                _year=str(datetime.now().year)
            msg = utils.generate_msg_xero_member_payments(f"{result[0][2]} ({result[0][1]})",member_code, _year)
            await message.reply(msg)
# --------------------------------------------------
@Client.on_message(filters.command(["xs"]))
@loggers.async_log_access
@bot_auth.async_management_only
async def finance_search_member_sub(client: Client, message: Message):
    member_code = None
    if len(message.command) >= 2:
        member_code = message.command[1].upper()
        # There is atleast a member code sent
        # Match member codes such as V019. One char followed by 2 or 3 digits
        if utils.is_valid_member_code(member_code) is None:
            msg = "Please enter a Member Code to search"
            await message.reply(msg,quote=True)
            return
    #A member code has been sent
    if member_code:
        result = db.get_member_details(member_code,'code')
        if len(result) == 0:
            await message.reply("No such Member")
            return  
        elif len(result) >= 1:
        # Figure out the year of accounts we want to retrieve 
        # /xs v019 2020. As of now, we only support current year
            if len(message.command) == 3:
                _year=message.command[2]
            # /x v019
            elif len(message.command) == 2:
                _year = str(datetime.now().year)    
            msg = utils.generate_msg_xero_member_invoices(member_code, _year)
            await message.reply(msg)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Executive Summary Button"))
@loggers.async_log_access
async def get_finance_executive_summary(client: Client, query: CallbackQuery):
    await query.answer()
    report = xero_utils.get_executive_summary()['Reports'][0]['Rows']
    msg = "???**EXECUTIVE SUMMARY**???\n\n"
    for row in report:
        if row['RowType'] == 'Header':
            current_month_title=row['Cells'][1]['Value']
            previous_month_title=row['Cells'][2]['Value']
        else:
            # There are multiple sections: Cash, Profitability etc. Loop through items in each
            logger.debug(f"In Section: {row['Title']}")
            # Ignore these sections; we're not interested
            if (row['Title'].upper() in ['POSITION','PERFORMANCE','PROFITABILITY','INCOME']):
                continue
            msg += f"**==========\n????SECTION: {row['Title'].upper()}**\n"
            for section in row['Rows']:
                logger.debug(f"Processing [{section['Cells'][0]['Value']}]")    
                msg += "???????????????\n"
                msg += f"**{section['Cells'][0]['Value']}**\n"
                current_month_value=section['Cells'][1]['Value']
                previous_month_value=section['Cells'][2]['Value']
                variance = section['Cells'][3]['Value']           
               
                msg += f"{previous_month_title}={previous_month_value if ('%' in previous_month_value or previous_month_value=='' ) else round(float(previous_month_value),1):,.2f}\n"
                msg += f"{current_month_title}={current_month_value if ('%' in current_month_value or current_month_value=='' ) else round(float(current_month_value),1):,.2f}\n"

                if variance[:1] == '-':
                    # Negative variance
                    msg += f"Variance=???{variance}\n"
                else:
                    msg += f"Variance=???{variance}\n"
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Bank Summary Button"))
@loggers.async_log_access
async def get_finance_bank_summary(client: Client, query: CallbackQuery):
    await query.answer()
    report=xero_utils.get_bank_summary()['Reports'][0]['Rows']
    msg="???**BANK ACCOUNTS SUMMARY**???\n\n"
    for row in report:
        if row['RowType'] == 'Header':
            opening_bal_title=row['Cells'][1]['Value']
            cash_recvd_title=row['Cells'][2]['Value']
            cash_spent_title=row['Cells'][3]['Value']
            closing_bal_title=row['Cells'][4]['Value']
        else:
            # For each Bank account
            all_fd_sum=0.0
            for _bank_account in row['Rows']:
                bank_account=_bank_account['Cells'][0]['Value']
                logger.debug(f"Processing [{bank_account}]")

                opening_bal_value=_bank_account['Cells'][1]['Value'] if _bank_account['Cells'][1]['Value'] != '' else 0
                cash_recvd_value=_bank_account['Cells'][2]['Value'] if _bank_account['Cells'][2]['Value'] != '' else 0
                cash_spent_value=_bank_account['Cells'][3]['Value'] if _bank_account['Cells'][3]['Value'] != '' else 0
                closing_bal_value=_bank_account['Cells'][4]['Value'] if _bank_account['Cells'][4]['Value'] != '' else 0

                if bank_account.startswith('DBS FD'):
                    # Sum up all FDs and skip loop
                    all_fd_sum += float(closing_bal_value)
                    continue

                if float(closing_bal_value)!=0:
                    # This is to ignore Cash, NETS and Suspense accounts where closing bal is usually 0
                    msg += "???????????????\n"
                    msg += f"**{bank_account}**\n"
                    msg += f"{opening_bal_title}=${float(opening_bal_value):,.2f}\n"
                    msg += f"{cash_recvd_title}=${float(cash_recvd_value):,.2f}\n"
                    msg += f"{cash_spent_title}=${float(cash_spent_value):,.2f}\n"                        
                    msg += f"**{closing_bal_title}=${float(closing_bal_value):,.2f}**\n"

    msg += "--------------------\n"
    msg += f"(Fixed Deposits=**${float(all_fd_sum):,.2f}**)\n"
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter_starts_with("Finance Trial Balance"))
@loggers.async_log_access
async def get_finance_trial_balance(client: Client, query: CallbackQuery):
    await query.answer()
    is_income_report = "REVENUE" in query.data.upper()
    msg="**TRIAL BALANCE**\n"
    msg+=f"`For Year {str(datetime.now().year)}`\n"
    msg += "?????????????????????\n\n"

    def __get_msg(rows, report_type):
        __msg = ""
        for row in rows:
            account=row['Cells'][0]['Value']
            logger.debug(f"Processing [{account}]")
            if report_type == 'revenue':
                ytd_value=row['Cells'][4]['Value'] if row['Cells'][4]['Value'] != '' else 0
            else:
                ytd_value=row['Cells'][3]['Value'] if row['Cells'][3]['Value'] != '' else 0

            __msg += f"{account}\n"
            __msg += f"**${float(ytd_value):,.2f}**\n"
            __msg += "????????????????????????????????????????????????????????????\n"
        # Remove last line
        __msg = __msg[:-len("????????????????????????????????????????????????????????????\n")]
        return __msg

    # report[1] = Revenue
    if is_income_report:
        report=xero_utils.xero_get_trial_balance(_paymentsOnly=True)['Reports'][0]['Rows']
        msg += __get_msg(report[1]['Rows'], report_type = 'revenue')        
    else:
        report=xero_utils.xero_get_trial_balance()['Reports'][0]['Rows']
        # report[2] = Expense
        msg += __get_msg(report[2]['Rows'], report_type = 'expense')

    # Telegram has a 4096 byte limit for msgs
    msg=(msg[:4076] + '\n`... (truncated)`') if len(msg) > 4096 else msg
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Payments WTD Button"))
@loggers.async_log_access
async def get_finance_payments_wtd_balance(client: Client, query: CallbackQuery):
    await query.answer()
    payments=xero_utils.xero_get_payments()
    msg="???**INVOICE/BILL PAYMENTS**???\n\n"
    
    for payment in payments['Payments']:
        if payment['Status'] != 'DELETED':
            if payment['Invoice']['Type'] == 'ACCPAY':
                inv_type_icon='???'
                icon='????'
            elif payment['Invoice']['Type'] == 'ACCREC':
                inv_type_icon='???'
                icon='????'
            _date=xero_utils.parse_Xero_Date(payment['Date'])
            msg += f"\n{icon} **{payment['Invoice']['Contact']['Name']}** ({payment['Invoice']['InvoiceNumber'] if payment['Invoice']['InvoiceNumber'] != '' else '-NA-'})\n"
            msg += f"`({_date:%Y-%m-%d})` "
            msg += f"**${payment['Amount']}** {inv_type_icon}\n"        

    # Telegram has a 4096 byte limit for msgs
    msg=(msg[:4076] + '\n`... (truncated)`') if len(msg) > 4096 else msg
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Latest Transactions Button"))
@loggers.async_log_access
async def get_finance_latest_tx(client: Client, query: CallbackQuery):
    await query.answer()
    bank_tx=xero_utils.xero_get_bank_transactions()
    msg="???**TRANSACTIONS (WTD)**???\n`No Invoice (subscription) or bill payment transactions shown`\n\n"

    for tx in bank_tx['BankTransactions']:
        _msg=''
        if tx['Type'] == 'RECEIVE':
            icon='????'
        elif tx['Type'] == 'SPEND':
            icon='????'
        elif tx['Type'] == 'SPEND-TRANSFER':
            icon='????'
            _msg=" `(Transfer Out)`"
        elif tx['Type'] == 'RECEIVE-TRANSFER':
            icon='????'
            _msg=" `(Transfer In)`"
        else:
            icon='???'\

        if 'Contact' in tx:
            msg += f"{icon} **{tx['Contact']['Name']}** "
        if tx['BankAccount']['Name'].upper() == 'CASH':
            msg += f"???? CASH {_msg}\n"
        elif 'DBS' in tx['BankAccount']['Name']:
            msg += f"???? DBS {_msg}\n"
        elif tx['BankAccount']['Name'].upper() == 'NETS':
            msg += f"???? NETS {_msg}\n"
        else:
            msg += f"\n\n{icon} **{tx['BankAccount']['Name']}** {_msg}\n"

        msg += f"`{xero_utils.parse_Xero_Date(tx['Date']):%Y-%m-%d}`\n"
        msg += f"**${tx['Total']}**\n\n"
    
    # Telegram has a 4096 byte limit for msgs
    msg=(msg[:4076] + '\n`... (truncated)`') if len(msg) > 4096 else msg
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Projects Button"))
@loggers.async_log_access
async def get_finance_tracking(client: Client, query: CallbackQuery):
    await query.answer()
    msg = utils.get_tracked_projects()
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)
