import logging
from datetime import datetime
from typing import cast

from pyrogram import Client, enums, filters, types
from pyrogram.errors import RichMessageUnsupported
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup

from stoscbots.bot import family_profile, keyboards
from stoscbots.db import db
from stoscbots.util import bot_auth, loggers, utils
from stoscbots.util.loggers import LOGLEVEL
from stoscbots.xero import xero_utils

logger = logging.getLogger("Handler.MyDetails")
logger.setLevel(LOGLEVEL)

LIST_ACCOUNTS = xero_utils.get_chart_of_accounts(class_type="REVENUE")
LIST_ACCOUNTS = [x for x in LIST_ACCOUNTS if x["Code"] != "3230"]  # Interest Income
LIST_ACCOUNTS = [x for x in LIST_ACCOUNTS if x["Code"] != "3231"]  # Fixed Deposit Interest


def _rich_text(value: str | list[str | types.RichText]) -> types.RichText:
    return cast(types.RichText, value)


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data,
    )


async def _send_rich_my_details_card(
    client: Client, chat_id: int, rich: types.InputRichMessage, fallback: str,
    reply_markup: InlineKeyboardMarkup = keyboards.back_to_my_details_keyboard,
) -> None:
    try:
        await client.send_rich_message(chat_id, rich, reply_markup=reply_markup)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich My Details card; sending plain text")
        await client.send_message(
            chat_id, fallback, parse_mode=enums.ParseMode.DISABLED,
            reply_markup=reply_markup,
        )


# ==================================================
# Callback Handlers (for Buttons)
@Client.on_callback_query(dynamic_data_filter("My Profile"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_my_profile(client: Client, query: CallbackQuery):
    await query.answer()
    member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    if not member_code:
        await query.answer("Could not find your registered member code.", show_alert=True)
        return
    result = db.get_member_details(member_code, "code")
    if not result:
        await query.answer(f"No family record found for {member_code}", show_alert=True)
        return
    await family_profile.send_family_profile(
        client,
        query.from_user.id,
        result[0],
        reply_markup=keyboards.back_to_my_details_keyboard,
        note="Please contact the church office or secretary@stscoc.com to update any details.",
    )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("My Contributions"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_my_contributions(client: Client, query: CallbackQuery):
    await query.answer()
    year = str(datetime.now().year)
    member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    if not member_code:
        await query.answer("Could not find your registered member code.", show_alert=True)
        return
    result = db.get_member_details(member_code, "code")
    name = f"{result[0][2]} ({result[0][1]})" if result else member_code
    fallback = utils.generate_msg_xero_member_payments(name, member_code, year)
    payments = utils.get_member_payments(member_code, year) or []

    blocks: list[types.InputRichBlock] = [
        types.InputRichBlockSectionHeading(text=_rich_text(f"Contributions ({year}) 💳"), size=3),
        types.InputRichBlockParagraph(text=_rich_text(name)),
    ]
    if not payments:
        blocks.append(types.InputRichBlockParagraph(
            text=_rich_text(f"No contributions recorded for {year}.")
        ))
    else:
        cells = [[
            types.RichBlockTableCell(text=_rich_text("Account"), is_header=True),
            types.RichBlockTableCell(text=_rich_text("Amount ($)"), is_header=True, align="right"),
        ]]
        total = 0.0
        for item in payments:
            account = item.get("Account", "Unknown")
            try:
                amt = float(item.get("LineAmount", 0))
            except (ValueError, TypeError):
                amt = 0.0
            total += amt
            cells.append([
                types.RichBlockTableCell(text=_rich_text(account)),
                types.RichBlockTableCell(text=_rich_text(f"{amt:,.2f}"), align="right"),
            ])
        blocks.append(types.InputRichBlockTable(cells=cells, is_striped=True, is_compact=True))
        latest_ts = max((item.get("modified_ts", "") for item in payments), default="")
        summary = f"Total: ${total:,.2f}"
        if latest_ts:
            summary += f" · As of {latest_ts[:16]}"
        blocks.append(types.InputRichBlockFooter(text=_rich_text(summary)))

    await _send_rich_my_details_card(
        client, query.from_user.id, types.InputRichMessage(blocks=blocks), fallback,
    )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("My Dues"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_my_subscriptions(client: Client, query: CallbackQuery):
    await query.answer()
    year = str(datetime.now().year)
    member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    if not member_code:
        await query.answer("Could not find your registered member code.", show_alert=True)
        return
    fallback = utils.generate_msg_xero_member_invoices(member_code, year)
    invoices_resp = xero_utils.get_Invoices(member_code)

    filtered = []
    if invoices_resp and "Invoices" in invoices_resp:
        for inv in invoices_resp["Invoices"]:
            if (
                inv.get("Type") == "ACCREC"
                and not inv.get("InvoiceNumber", "").endswith("-VOID")
                and (
                    inv.get("InvoiceNumber", "").startswith(f"INV-{year[2:]}")
                    or inv.get("InvoiceNumber", "").startswith(f"HF-{year[2:]}")
                    or (inv.get("Status") == "AUTHORISED" and int(str(inv.get("DateString", "0")).split("-")[0]) <= int(year))
                )
            ):
                filtered.append(inv)

    due_invoices = [
        inv for inv in filtered
        if float(inv.get("AmountDue", 0)) > 0 or inv.get("Status") == "AUTHORISED"
    ]
    total_due = sum(float(inv.get("AmountDue", 0)) for inv in due_invoices)

    blocks: list[types.InputRichBlock] = [
        types.InputRichBlockSectionHeading(text=_rich_text("Outstanding Dues 📜"), size=3),
        types.InputRichBlockParagraph(text=_rich_text(f"Family code: {member_code} · {year}")),
    ]
    if not due_invoices or total_due == 0:
        blocks.append(types.InputRichBlockParagraph(
            text=_rich_text("All subscriptions and dues are up to date! 🟢")
        ))
        markup = keyboards.back_to_my_details_keyboard
    else:
        cells = [[
            types.RichBlockTableCell(text=_rich_text("Invoice"), is_header=True),
            types.RichBlockTableCell(text=_rich_text("Description"), is_header=True),
            types.RichBlockTableCell(text=_rich_text("Due ($)"), is_header=True, align="right"),
        ]]
        for inv in due_invoices:
            inv_num = inv.get("InvoiceNumber") or "—"
            items = inv.get("LineItems") or []
            desc = ", ".join(l.get("Description", "") for l in items if l.get("Description")) or "Subscription"
            due_val = float(inv.get("AmountDue", 0))
            cells.append([
                types.RichBlockTableCell(text=_rich_text(inv_num)),
                types.RichBlockTableCell(text=_rich_text(desc)),
                types.RichBlockTableCell(text=_rich_text(f"{due_val:,.2f}"), align="right"),
            ])
        blocks.append(types.InputRichBlockTable(cells=cells, is_striped=True, is_compact=True))
        blocks.append(types.InputRichBlockFooter(text=_rich_text(f"Total Due: ${total_due:,.2f}")))
        markup = keyboards.dues_payment_keyboard

    await _send_rich_my_details_card(
        client, query.from_user.id, types.InputRichMessage(blocks=blocks), fallback,
        reply_markup=markup,
    )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("List of Accounts"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_list_accounts(client: Client, query: CallbackQuery):
    await query.answer()
    year = str(datetime.now().year)
    member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    payments = utils.get_member_payments(member_code, year) if member_code else []
    payments = payments or []

    paid_map = {}
    for payment in payments:
        code_part = payment.get("AccountCode", "").split("_")
        if len(code_part) > 1:
            try:
                paid_map[code_part[1]] = float(payment.get("LineAmount", 0))
            except (ValueError, TypeError):
                pass

    fallback_lines = ["**List of Accounts**\n➖➖➖➖➖➖\nYou may contribute towards the following accounts:\n"]
    for account in LIST_ACCOUNTS:
        acct_code = account.get("Code")
        if acct_code in paid_map:
            fallback_lines.append(f"• **{account['Name']} `(${paid_map[acct_code]:,.0f})`**")
        else:
            fallback_lines.append(f"• {account['Name']}")
    fallback_lines.append("\n__**Bold** indicates that you have contributed towards this account head__")
    fallback = "\n".join(fallback_lines)

    blocks: list[types.InputRichBlock] = [
        types.InputRichBlockSectionHeading(text=_rich_text("Church Accounts & Giving ℹ"), size=3),
        types.InputRichBlockParagraph(text=_rich_text(f"Eligible contribution heads for {year}:")),
    ]
    cells = [[
        types.RichBlockTableCell(text=_rich_text("Account"), is_header=True),
        types.RichBlockTableCell(text=_rich_text(f"Contributed ({year})"), is_header=True, align="right"),
    ]]
    for account in LIST_ACCOUNTS:
        acct_code = account.get("Code")
        acct_name = account.get("Name", "")
        if acct_code in paid_map:
            cells.append([
                types.RichBlockTableCell(text=_rich_text(types.RichTextBold(text=_rich_text(acct_name)))),
                types.RichBlockTableCell(
                    text=_rich_text(types.RichTextBold(text=_rich_text(f"${paid_map[acct_code]:,.0f}"))),
                    align="right",
                ),
            ])
        else:
            cells.append([
                types.RichBlockTableCell(text=_rich_text(acct_name)),
                types.RichBlockTableCell(text=_rich_text("—"), align="right"),
            ])
    blocks.append(types.InputRichBlockTable(cells=cells, is_striped=True, is_compact=True))
    blocks.append(types.InputRichBlockFooter(
        text=_rich_text("Quote your family code and account name in PayNow or bank transfer references.")
    ))

    await _send_rich_my_details_card(
        client, query.from_user.id, types.InputRichMessage(blocks=blocks), fallback,
    )
