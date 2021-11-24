from pyrogram import Client, filters
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from stoscbots.bot import keyboards
from stoscbots.xero import xero_utils
import re
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
@Client.on_message(filters.command(["x"]))
@loggers.log_access
@bot_auth.management_only
def finance_search_member_payments(client, message):
    if len(message.command) != 2:
        msg="Please enter a Member Code to search"
        message.reply(msg,quote=True)
        return
    member_code = message.command[1]
    # Match member codes such as V019. One char followed by 2 or 3 digits
    if (re.match('[A-Za-z]\d{2,3}', member_code) is not None):
        #A member code has been sent
        result=db.get_member_details(member_code, 'code')
        if len(result) == 0:
            message.reply("No such Member")
            return  
        elif len(result) >= 1:              
            # Figure out the year of accounts we want to retrieve 
            # /x v019 2020
            if len(message.command) == 3:
                _year=message.command[2]
            # /x v019
            elif len(message.command) == 2:
                _year=str(datetime.now().year)    
            msg = utils.generate_msg_xero_member_payments(member_code, _year)
            message.reply(msg)
    else:
        message.reply("Invalid Member Code")
# --------------------------------------------------
@Client.on_message(filters.command(["xs"]))
@loggers.log_access
@bot_auth.management_only
def finance_search_member_sub(client, message):
    if len(message.command) != 2:
        msg="Please enter a Member Code to search"
        message.reply(msg,quote=True)
        return
    member_code = message.command[1].upper()
    # Match member codes such as V019. One char followed by 2 or 3 digits
    if (re.match('[A-Za-z]\d{2,3}', member_code) is not None):
        #A member code has been sent
        result=db.get_member_details(member_code,'code')
        if len(result) == 0:
            message.reply("No such Member")
            return  
        msg = utils.generate_msg_xero_member_invoices(member_code, '2021')
        message.reply(msg)
    else:
        message.reply("Invalid Member Code")
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Executive Summary Button"))
@loggers.log_access
def get_finance_executive_summary(client, query):
    query.answer()
    report=xero_utils.get_executive_summary()['Reports'][0]['Rows']
    msg="➖**EXECUTIVE SUMMARY**➖\n\n"
    for row in report:
        if row['RowType'] == 'Header':
            current_month_title=row['Cells'][1]['Value']
            previous_month_title=row['Cells'][2]['Value']
        else:
            # There are multiple sections: Cash, Profitability etc. Loop through items in each
            loggers.debug(f"In Section: {row['Title']}")
            # Ignore these sections; we're not interested
            if (row['Title'].upper() in ['POSITION','PERFORMANCE','PROFITABILITY','INCOME']):
                continue
            msg += f"**==========\n📌SECTION: {row['Title'].upper()}**\n"
            for section in row['Rows']:
                loggers.debug(f"Processing [{section['Cells'][0]['Value']}]")    
                msg += "〰〰〰〰〰\n"
                msg += f"**{section['Cells'][0]['Value']}**\n"
                current_month_value=section['Cells'][1]['Value']
                previous_month_value=section['Cells'][2]['Value']
                variance=section['Cells'][3]['Value']           
               
                msg += f"{previous_month_title}={previous_month_value if ('%' in previous_month_value or previous_month_value=='' ) else round(float(previous_month_value),1):,.2f}\n"
                msg += f"{current_month_title}={current_month_value if ('%' in current_month_value or current_month_value=='' ) else round(float(current_month_value),1):,.2f}\n"

                if variance[:1] == '-':
                    # Negative variance
                    msg += f"Variance=▼{variance}\n"
                else:
                    msg += f"Variance=▲{variance}\n"
    utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Bank Summary Button"))
@loggers.log_access
def get_finance_bank_summary(client, query):
    query.answer()
    report=xero_utils.get_bank_summary()['Reports'][0]['Rows']
    msg="➖**BANK ACCOUNTS SUMMARY**➖\n\n"
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
                loggers.debug(f"Processing [{bank_account}]")

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
                    msg += "〰〰〰〰〰\n"
                    msg += f"**{bank_account}**\n"
                    msg += f"{opening_bal_title}=${float(opening_bal_value):,.2f}\n"
                    msg += f"{cash_recvd_title}=${float(cash_recvd_value):,.2f}\n"
                    msg += f"{cash_spent_title}=${float(cash_spent_value):,.2f}\n"                        
                    msg += f"**{closing_bal_title}=${float(closing_bal_value):,.2f}**\n"

    msg += "--------------------\n"
    msg += f"(Fixed Deposits=**${float(all_fd_sum):,.2f}**)\n"
    utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Trial Balance Button"))
@loggers.log_access
def get_finance_trial_balance(client, query):
    query.answer()
    report=xero_utils.xero_get_trial_balance()['Reports'][0]['Rows']
    msg="➖**TRIAL BALANCE**➖\n\n"
    for row in report:
        if row['RowType'] == 'Header':
            debit_ytd_title=row['Cells'][3]['Value']
            credit_ytd_title=row['Cells'][4]['Value']
        else:
            # For each Bank account
            for _section in row['Rows']:
                section=_section['Cells'][0]['Value']
                loggers.debug(f"Processing [{section}]")

                debit_ytd_value=_section['Cells'][3]['Value'] if _section['Cells'][3]['Value'] != '' else 0
                credit_ytd_value=_section['Cells'][4]['Value'] if _section['Cells'][4]['Value'] != '' else 0

                if not section.startswith('DBS FD'):
                    msg += "〰〰〰〰〰\n"
                    msg += f"**{section}**\n"
                    if float(debit_ytd_value) != 0.0:
                        msg += f"{debit_ytd_title}=${float(debit_ytd_value):,.2f}\n"
                    if float(credit_ytd_value) != 0.0:
                        msg += f"{credit_ytd_title}=${float(credit_ytd_value):,.2f}\n"

    # Telegram has a 4096 byte limit for msgs
    msg=(msg[:4076] + '\n`... (truncated)`') if len(msg) > 4096 else msg
    utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Payments WTD Button"))
@loggers.log_access
def get_finance_payments_wtd_balance(client, query):
    query.answer()
    payments=xero_utils.xero_get_payments()
    msg="➖**INVOICE/BILL PAYMENTS**➖\n\n"
    
    for payment in payments['Payments']:
        if payment['Status'] != 'DELETED':
            if payment['Invoice']['Type'] == 'ACCPAY':
                inv_type_icon='⇨'
                icon='🔴'
            elif payment['Invoice']['Type'] == 'ACCREC':
                inv_type_icon='⇦'
                icon='🟢'
            _date=xero_utils.parse_Xero_Date(payment['Date'])
            msg += f"\n{icon} **{payment['Invoice']['Contact']['Name']}** ({payment['Invoice']['InvoiceNumber'] if payment['Invoice']['InvoiceNumber'] != '' else '-NA-'})\n"
            msg += f"`({_date:%Y-%m-%d})` "
            msg += f"**${payment['Amount']}** {inv_type_icon}\n"        

    # Telegram has a 4096 byte limit for msgs
    msg=(msg[:4076] + '\n`... (truncated)`') if len(msg) > 4096 else msg
    utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Latest Transactions Button"))
@loggers.log_access
def get_finance_latest_tx(client, query):
    query.answer()
    bank_tx=xero_utils.xero_get_bank_transactions()
    msg="➖**TRANSACTIONS (WTD)**➖\n`No Invoice (subscription) or bill payment transactions shown`\n\n"

    for tx in bank_tx['BankTransactions']:
        _msg=''
        if tx['Type'] == 'RECEIVE':
            icon='🟢'
        elif tx['Type'] == 'SPEND':
            icon='🔴'
        elif tx['Type'] == 'SPEND-TRANSFER':
            icon='🔴'
            _msg=f" `(Transfer Out)`"
        elif tx['Type'] == 'RECEIVE-TRANSFER':
            icon='🟢'
            _msg=f" `(Transfer In)`"
        else:
            icon='❓'\

        if 'Contact' in tx:
            msg += f"{icon} **{tx['Contact']['Name']}** "
        if tx['BankAccount']['Name'].upper() == 'CASH':
            msg += f"💵 CASH {_msg}\n"
        elif 'DBS' in tx['BankAccount']['Name']:
            msg += f"🏦 DBS {_msg}\n"
        elif tx['BankAccount']['Name'].upper() == 'NETS':
            msg += f"💳 NETS {_msg}\n"
        else:
            msg += f"\n\n{icon} **{tx['BankAccount']['Name']}** {_msg}\n"

        msg += f"`{xero_utils.parse_Xero_Date(tx['Date']):%Y-%m-%d}`\n"
        msg += f"**${tx['Total']}**\n\n"        
    
    # Telegram has a 4096 byte limit for msgs
    msg=(msg[:4076] + '\n`... (truncated)`') if len(msg) > 4096 else msg
    utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Help Button"))
@loggers.log_access
def get_finance_help(client, query):
    query.answer()
    msg="🚨 Get member Balances by **member ID** or **Name**. \n Examples:\n‣ Payments by member code: `/x A001`\n‣ Subscriptions by member code: `/xs A001`"
    utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)