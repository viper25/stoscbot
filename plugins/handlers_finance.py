import logging
from datetime import datetime

from pyrogram import Client, enums, filters
from pyrogram.errors import RichMessageUnsupported
from pyrogram.types import CallbackQuery, LinkPreviewOptions, Message

from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import bot_auth, loggers, utils
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


def _format_member_name(result_row: list, member_code: str) -> str:
    if not result_row:
        return member_code
    head_name = result_row[2] if len(result_row) > 2 and result_row[2] else (result_row[0] if len(result_row) > 0 and result_row[0] else member_code)
    family_name = result_row[1] if len(result_row) > 1 and result_row[1] else ""
    return f"{head_name} ({family_name})" if family_name else str(head_name)


async def _send_member_payments_card(client: Client, chat_id: int, member_code: str, year: str, result_row: list):
    name = _format_member_name(result_row, member_code)
    try:
        payments = utils.get_member_payments(member_code, year) or []
    except Exception as exc:
        logger.error("Failed to fetch payments for %s: %s", member_code, exc)
        await client.send_message(
            chat_id,
            f"⚠️ Unable to fetch contributions for **{member_code}** at this moment. Please try again later.",
        )
        return

    markup = keyboards.get_member_finance_search_keyboard(member_code, year, "payments")
    fallback = utils.generate_msg_xero_member_payments(name, member_code, year)
    try:
        rich_card = keyboards.get_rich_member_payments(name, member_code, year, payments)
        await client.send_rich_message(chat_id, rich_card, reply_markup=markup)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected rich member payments card; sending plain text")
        await client.send_message(
            chat_id,
            fallback,
            reply_markup=markup,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


async def _send_member_invoices_card(client: Client, chat_id: int, member_code: str, year: str, result_row: list):
    name = _format_member_name(result_row, member_code)
    try:
        invoices_resp = xero_utils.get_Invoices(member_code) or {}
    except Exception as exc:
        logger.error("Failed to fetch invoices for %s: %s", member_code, exc)
        await client.send_message(
            chat_id,
            f"⚠️ Unable to fetch invoices for **{member_code}** at this moment. Please try again later.",
        )
        return

    markup = keyboards.get_member_finance_search_keyboard(member_code, year, "invoices")
    fallback = utils.generate_msg_xero_member_invoices(member_code, year)
    try:
        rich_card = keyboards.get_rich_member_invoices(name, member_code, year, invoices_resp)
        await client.send_rich_message(chat_id, rich_card, reply_markup=markup)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected rich member invoices card; sending plain text")
        await client.send_message(
            chat_id,
            fallback,
            reply_markup=markup,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


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
        await _send_member_payments_card(client, message.chat.id, member_code, year, result[0])
    elif message.command[0] == "xs":
        await _send_member_invoices_card(client, message.chat.id, member_code, year, result[0])


# --------------------------------------------------
@Client.on_callback_query(filters.regex(r"^search_xero_(payments|dues):([A-Z0-9]+):([0-9]{4})$"))
@loggers.async_log_access
@bot_auth.async_management_only
async def finance_search_member_callback(client: Client, query: CallbackQuery):
    await query.answer()
    if not query.matches:
        return
    action = query.matches[0].group(1)
    member_code = query.matches[0].group(2)
    year = query.matches[0].group(3)

    result = db.get_member_details(member_code, 'code')
    if not result:
        await query.answer(f"No such Member: {member_code}", show_alert=True)
        return

    if action == "payments":
        await _send_member_payments_card(client, query.from_user.id, member_code, year, result[0])
    elif action == "dues":
        await _send_member_invoices_card(client, query.from_user.id, member_code, year, result[0])


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Executive Summary Button"))
@loggers.async_log_access
@bot_auth.async_management_only
async def get_finance_executive_summary(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    try:
        report = xero_utils.get_executive_summary()['Reports'][0]['Rows']
    except Exception as exc:
        logger.error("Failed to fetch executive summary from Xero: %s", exc)
        await client.send_message(
            chat_id,
            "⚠️ Unable to fetch Executive Summary from Xero at this moment. Please try again later.",
            reply_markup=keyboards.finance_menu_keyboard,
        )
        return

    # Plain text fallback generator
    variance_symbols = {"-": "▼", "": "▲"}

    def format_value(value):
        return f"{value if ('%' in value or value == '') else round(float(value), 1):,.2f}"

    filtered_rows = [row for row in report if
                     row.get('Title', '').upper() not in ['POSITION', 'PERFORMANCE', 'PROFITABILITY', 'INCOME']]

    current_month_title = "Current"
    previous_month_title = "Previous"
    msg_parts = ["➖**EXECUTIVE SUMMARY**➖\n\n"]
    for row in filtered_rows:
        if row.get('RowType') == 'Header':
            current_month_title = row['Cells'][1]['Value']
            previous_month_title = row['Cells'][2]['Value']
        else:
            msg_parts.append(f"**==========\n📌SECTION: {row.get('Title', '').upper()}**\n")
            for section in row.get('Rows', []):
                msg_parts.extend([
                    "〰〰〰〰〰\n",
                    f"**{section['Cells'][0]['Value']}**\n",
                    f"{previous_month_title}={format_value(section['Cells'][2]['Value'])}\n",
                    f"{current_month_title}={format_value(section['Cells'][1]['Value'])}\n",
                    f"Variance={variance_symbols.get(section['Cells'][3]['Value'][:1], '▲')}{section['Cells'][3]['Value']}\n"
                ])
    fallback_text = ''.join(msg_parts)

    try:
        rich_card = keyboards.get_rich_finance_executive_summary(report)
        await client.send_rich_message(
            chat_id,
            rich_card,
            reply_markup=keyboards.finance_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich executive summary card; sending plain text")
        await client.send_message(
            chat_id,
            fallback_text,
            reply_markup=keyboards.finance_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Bank Summary Button"))
@loggers.async_log_access
@bot_auth.async_management_only
async def get_finance_bank_summary(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    try:
        report = xero_utils.get_bank_summary()['Reports'][0]['Rows']
    except Exception as exc:
        logger.error("Failed to fetch bank summary from Xero: %s", exc)
        await client.send_message(
            chat_id,
            "⚠️ Unable to fetch Bank Summary from Xero at this moment. Please try again later.",
            reply_markup=keyboards.finance_menu_keyboard,
        )
        return

    # Plain text fallback generator
    header = None
    msg_parts = ["➖**BANK ACCOUNTS SUMMARY**➖\n\n"]
    all_fd_sum = 0.0

    def format_bank_account_data(bank_account_data, hdr):
        closing_bal_value = bank_account_data['Cells'][4]['Value'] or '0'
        return f"""
〰〰〰〰〰
**{bank_account_data['Cells'][0]['Value']}**
{hdr['Cells'][1]['Value']}=${float(bank_account_data['Cells'][1]['Value'] or '0'):,.2f}
{hdr['Cells'][2]['Value']}=${float(bank_account_data['Cells'][2]['Value'] or '0'):,.2f}
{hdr['Cells'][3]['Value']}=${float(bank_account_data['Cells'][3]['Value'] or '0'):,.2f}
**{hdr['Cells'][4]['Value']}=${float(closing_bal_value):,.2f}**
"""

    for row in report:
        if row.get('RowType') == 'Header':
            header = row
        else:
            for bank_account_data in row.get('Rows', []):
                bank_account = bank_account_data['Cells'][0]['Value']
                closing_bal_value = bank_account_data['Cells'][4]['Value'] or '0'

                if bank_account.startswith('DBS FD'):
                    all_fd_sum += float(closing_bal_value)
                    continue

                if float(closing_bal_value) != 0 and header:
                    msg_parts.append(format_bank_account_data(bank_account_data, header))

    msg_parts.append("--------------------\n")
    msg_parts.append(f"(Fixed Deposits=**${float(all_fd_sum):,.2f}**)\n")
    fallback_text = ''.join(msg_parts)

    try:
        rich_card = keyboards.get_rich_finance_bank_summary(report)
        await client.send_rich_message(
            chat_id,
            rich_card,
            reply_markup=keyboards.finance_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich bank summary card; sending plain text")
        await client.send_message(
            chat_id,
            fallback_text,
            reply_markup=keyboards.finance_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter_starts_with("Finance Trial Balance"))
@loggers.async_log_access
@bot_auth.async_management_only
async def get_finance_trial_balance(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    is_income_report = "REVENUE" in query.data.upper()

    try:
        tb_data = xero_utils.xero_get_trial_balance(_paymentsOnly=is_income_report)
        report = (tb_data or {}).get("Reports", [{}])[0].get("Rows", [])
        if not report:
            raise ValueError("Empty report data from Xero")
    except Exception as exc:
        logger.error("Failed to fetch trial balance from Xero: %s", exc)
        await client.send_message(
            chat_id,
            "⚠️ Unable to fetch Trial Balance from Xero at this moment. Please try again later.",
            reply_markup=keyboards.finance_menu_keyboard,
        )
        return

    # Plain text fallback generator
    report_type_name = "REVENUE" if is_income_report else "EXPENSE"
    val_index = 4 if is_income_report else 3
    _title, section_rows = keyboards._get_trial_balance_section(report, is_income_report)

    msg_items = []
    total_val = 0.0
    for row in section_rows:
        cells = row.get("Cells", [])
        if not cells or len(cells) <= val_index:
            continue
        name = str(cells[0].get("Value") or "").strip()
        if not name or row.get("RowType") == "Header":
            continue
        try:
            amt = float(cells[val_index].get("Value") or 0)
        except (ValueError, TypeError):
            amt = 0.0
        if row.get("RowType") in ("SummaryRow", "Total") or name.lower().startswith("total"):
            total_val = amt
            continue
        if amt != 0.0:
            msg_items.append(f"{name}\n**${amt:,.2f}**\n––––————————————————")

    rows_text = "\n".join(msg_items) if msg_items else "~ No entries ~"
    bullet = "🔹" if is_income_report else "🔸"
    fallback_text = (
        f"**TRIAL BALANCE — {report_type_name}**\n"
        f"`For Year {datetime.now().year}`\n"
        "➖➖➖➖➖➖➖\n\n"
        f"{rows_text}\n\n"
        f"{bullet} **Total {report_type_name.title()}: ${total_val:,.2f}**"
    )
    fallback_text = format_telegram_message(fallback_text)

    try:
        rich_card = keyboards.get_rich_finance_trial_balance(report, is_income_report)
        await client.send_rich_message(
            chat_id,
            rich_card,
            reply_markup=keyboards.finance_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich trial balance card; sending plain text")
        await client.send_message(
            chat_id,
            fallback_text,
            reply_markup=keyboards.finance_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Payments WTD Button"))
@loggers.async_log_access
@bot_auth.async_management_only
async def get_finance_payments_wtd_balance(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    try:
        payments = xero_utils.xero_get_payments()
    except Exception as exc:
        logger.error("Failed to fetch payments from Xero: %s", exc)
        await client.send_message(
            chat_id,
            "⚠️ Unable to fetch Payments from Xero at this moment. Please try again later.",
            reply_markup=keyboards.finance_menu_keyboard,
        )
        return

    msg_list = ["➖**INVOICE/BILL PAYMENTS**➖\n\n"]

    for payment in (payments or {}).get('Payments', []):
        if payment.get('Status') == 'DELETED':
            continue

        inv = payment.get('Invoice') or {}
        inv_type = inv.get('Type', '')
        inv_type_icon = '⇨' if inv_type == 'ACCPAY' else '⇦' if inv_type == 'ACCREC' else ''
        icon = '🔸' if inv_type == 'ACCPAY' else '🔹' if inv_type == 'ACCREC' else ''
        try:
            _date = xero_utils.parse_Xero_Date(payment['Date'])
            date_str = f"{_date:%Y-%m-%d}"
        except Exception:
            date_str = str(payment.get('Date', ''))
        contact_name = (inv.get('Contact') or {}).get('Name', 'Contact')
        invoice_number = inv.get('InvoiceNumber') or '-NA-'
        amount = payment.get('Amount', 0)

        msg_list.append(f"\n{icon} **{contact_name}** ({invoice_number})\n")
        msg_list.append(f"`({date_str})` ")
        msg_list.append(f"**${amount}** {inv_type_icon}\n")

    fallback_text = format_telegram_message(''.join(msg_list))

    try:
        rich_card = keyboards.get_rich_finance_payments_wtd(payments)
        await client.send_rich_message(
            chat_id,
            rich_card,
            reply_markup=keyboards.finance_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich payments WTD card; sending plain text")
        await client.send_message(
            chat_id,
            fallback_text,
            reply_markup=keyboards.finance_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------

@Client.on_callback_query(dynamic_data_filter("Finance Latest Transactions Button"))
@loggers.async_log_access
@bot_auth.async_management_only
async def get_finance_latest_tx(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    try:
        bank_tx = xero_utils.xero_get_bank_transactions()
    except Exception as exc:
        logger.error("Failed to fetch bank transactions from Xero: %s", exc)
        await client.send_message(
            chat_id,
            "⚠️ Unable to fetch Bank Transactions from Xero at this moment. Please try again later.",
            reply_markup=keyboards.finance_menu_keyboard,
        )
        return

    now = datetime.now()
    msg_parts = ["➖**TRANSACTIONS (WTD)**➖\n`No Invoice (subscription) or bill payment transactions shown`\n\n"]

    for tx in (bank_tx or {}).get('BankTransactions', []):
        try:
            tx_date = xero_utils.parse_Xero_Date(tx['Date'])
        except Exception:
            tx_date = now

        if tx_date > now:
            continue

        tx_type = tx.get('Type', '')
        _msg = ''
        if tx_type == 'RECEIVE':
            icon = '🔹'
        elif tx_type in {'SPEND', 'SPEND-TRANSFER'}:
            icon = '🔸'
            if tx_type == 'SPEND-TRANSFER':
                _msg = " `(Transfer Out)`"
        elif tx_type == 'RECEIVE-TRANSFER':
            icon = '🔹'
            _msg = " `(Transfer In)`"
        else:
            icon = '❓'

        contact_name = (tx.get('Contact') or {}).get('Name')
        if contact_name:
            msg_parts.append(f"{icon} **{contact_name}** ")

        bank_account_name = str((tx.get('BankAccount') or {}).get('Name', '')).upper()
        if bank_account_name == 'CASH':
            msg_parts.append(f"💵 CASH {_msg}\n")
        elif 'DBS' in bank_account_name:
            msg_parts.append(f"🏦 DBS {_msg}\n")
        elif bank_account_name == 'NETS':
            msg_parts.append(f"💳 NETS {_msg}\n")
        else:
            msg_parts.append(f"\n\n{icon} **{bank_account_name}** {_msg}\n")

        msg_parts.append(f"`{tx_date:%Y-%m-%d}`\n")
        msg_parts.append(f"**${tx.get('Total', 0)}**\n\n")

    fallback_text = format_telegram_message(''.join(msg_parts))

    try:
        rich_card = keyboards.get_rich_finance_latest_tx(bank_tx)
        await client.send_rich_message(
            chat_id,
            rich_card,
            reply_markup=keyboards.finance_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich latest transactions card; sending plain text")
        await client.send_message(
            chat_id,
            fallback_text,
            reply_markup=keyboards.finance_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Projects Button"))
@loggers.async_log_access
@bot_auth.async_management_only
async def get_finance_tracking(client: Client, query: CallbackQuery):
    await query.answer()
    msg = utils.get_tracked_projects()
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Finance Outstanding Button"))
@loggers.async_log_access
@bot_auth.async_management_only
async def get_finance_outstandings(client: Client, query: CallbackQuery):
    await query.answer()
    msg = utils.get_outstandings()
    logger.info(f"Got oustandings: {len(msg)} rows.")
    client.set_parse_mode(enums.ParseMode.MARKDOWN)
    await utils.edit_and_send_msg(query, msg, keyboards.finance_menu_keyboard)
