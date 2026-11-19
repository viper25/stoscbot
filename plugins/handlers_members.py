import logging
import math
import re
from collections.abc import Iterable
from datetime import date
from typing import cast

from pyrogram import Client, enums, filters, types
from pyrogram.errors import RichMessageUnsupported
from pyrogram.types import CallbackQuery

from stoscbots.bot import family_profile, keyboards
from stoscbots.db import db
from stoscbots.util import bot_auth, loggers, utils
from stoscbots.util.loggers import LOGLEVEL

# ==================================================
'''
Handle multiple callback queries data and return filter for each
'''

logger = logging.getLogger('Handler.Members')
logger.setLevel(LOGLEVEL)


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data  # "data" kwarg is accessed with "flt.data" above
    )


async def _send_members_card(
    client: Client, chat_id: int, heading: str, body: list[str | types.RichText], plain_body: str,
) -> None:
    rich = types.InputRichMessage(blocks=[
        types.InputRichBlockParagraph(text=types.RichTextBold(cast(types.RichText, heading))),
        types.InputRichBlockParagraph(text=cast(types.RichText, body)),
    ])
    try:
        await client.send_rich_message(chat_id, rich, reply_markup=keyboards.back_to_members_keyboard)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich Members card; sending plain text")
        await client.send_message(
            chat_id, f"{heading}\n\n{plain_body}", parse_mode=enums.ParseMode.DISABLED,
            reply_markup=keyboards.back_to_members_keyboard,
        )


async def _send_members_list(
    client: Client, chat_id: int, heading: str, rows: Iterable[tuple[str, str, str]],
    *, subtitle: str = "", empty: str = "No results",
) -> None:
    """Render (family code, name or label, years) rows; code and years may be empty."""
    text_lines = [subtitle] if subtitle else []
    body: list[str | types.RichText] = [subtitle] if subtitle else []
    has_rows = False
    for code, label, years in rows:
        has_rows = True
        code = code.strip()
        label = label.strip()
        suffix = f" - {years}" if years else ""
        if body:
            body.append("\n")
        if code:
            body.extend([f"• {label} (", family_profile.family_code_link(code), f"){suffix}"])
        else:
            body.append(f"• {label}{suffix}")
        text_lines.append(f"• {label}{f' ({code})' if code else ''}{suffix}")
    if not has_rows:
        if body:
            body.append("\n")
        body.append(empty)
        text_lines.append(empty)
    await _send_members_card(client, chat_id, heading, body, "\n".join(text_lines))


def _birthday_age(birthday: str, current_year: int) -> str:
    parts = birthday.split("/")
    year = int(parts[2]) if len(parts) == 3 and parts[2].isdecimal() else 0
    return str(current_year - year) if 0 < year <= current_year else "NA"


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Member Birthday Today Button"))
@loggers.async_log_access
@bot_auth.async_member_only
async def get_today_bdays(client: Client, query: CallbackQuery):
    await query.answer()
    _, _, result = db.get_bday('d')
    if not result:
        await utils.edit_and_send_msg(query, "No Birthdays today", keyboards.back_to_members_keyboard)
        return

    current_year = date.today().year
    rows = ((code, name, _birthday_age(birthday, current_year)) for code, name, birthday, _ in result)
    await _send_members_list(client, query.from_user.id, "Birthdays today 🎂", rows)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Member Anniversary Today Button"))
@loggers.async_log_access
@bot_auth.async_member_only
async def get_today_anniversaries(client: Client, query: CallbackQuery):
    await query.answer()
    _, _, result = db.get_anniversaries('d')
    if not result:
        await utils.edit_and_send_msg(query, "No Wedding Anniversary today", keyboards.back_to_members_keyboard)
        return

    current_year = date.today().year
    rows = [
        (code, name, str(current_year - wedding.year) if wedding.year != 1900 and wedding.year < current_year else "NA")
        for code, name, wedding in result
    ]
    await _send_members_list(client, query.from_user.id, "Wedding anniversaries today 💍", rows)


# --------------------------------------------------
@Client.on_message(filters.command(["bday"]))  # For when we want to print bdays without age
@Client.on_callback_query(dynamic_data_filter("Member Birthday Week Button"))
@loggers.async_log_access
async def get_weeks_bdays(client: Client, query_or_msg):
    is_callback = isinstance(query_or_msg, CallbackQuery)
    if is_callback:
        if not bot_auth.is_member(query_or_msg.from_user.id):
            await bot_auth.send_access_denied_msg(client, query_or_msg)
            return
        await query_or_msg.answer()
    start, end, result = db.get_bday('w')
    if is_callback:
        current_year = date.today().year
        rows = ((code, name, _birthday_age(birthday, current_year)) for code, name, birthday, _ in result)
        await _send_members_list(
            client, query_or_msg.from_user.id, "Birthdays this week 🎂", rows,
            subtitle=f"{start} – {end}", empty="No birthdays this week",
        )
        return

    if len(result) == 0:
        msg = " No Birthdays this week"
    else:
        msg = ">**Birthdays this week** 🎂\n"
        msg += f">`({start} - {end})`\n\n"
        for _item in result:
            _splits = _item[2].split('/')
            _day = _splits[0].zfill(2)
            _month = _splits[1].zfill(2)
            if _day == date.today().strftime("%d") and _month == date.today().strftime("%m"):
                msg += f"•** {_item[1].strip()}** `({_item[0].strip()})`\n"
            else:
                msg += f"• {_item[1].strip()} `({_item[0].strip()})`\n"
    await query_or_msg.reply_text(msg)


# --------------------------------------------------
@Client.on_message(filters.command(["anniv"]))  # For when we want to print bdays without age
@Client.on_callback_query(dynamic_data_filter("Member Anniversary Week Button"))
@loggers.async_log_access
async def get_weeks_anniversaries(client: Client, query_or_msg):
    is_callback = isinstance(query_or_msg, CallbackQuery)
    if is_callback:
        if not bot_auth.is_member(query_or_msg.from_user.id):
            await bot_auth.send_access_denied_msg(client, query_or_msg)
            return
        await query_or_msg.answer()

    start, end, result = db.get_anniversaries('w')
    today = date.today()
    if is_callback:
        rows = (
            (code, name, f"{today.year - wedding.year} yrs" if wedding.year != 1900 else "NA")
            for code, name, wedding in result
        )
        await _send_members_list(
            client, query_or_msg.from_user.id, "Wedding anniversaries this week 💍", rows,
            subtitle=f"{start} – {end}", empty="No wedding anniversaries this week",
        )
        return

    if len(result) == 0:
        msg = " No Wedding Anniversaries this week"
    else:
        msg_parts = [">**Wedding Anniversary** 💍\n", f">`({start} - {end})`\n\n"]
        for _item in result:
            name = _item[1].strip()
            code = _item[0].strip()
            if _item[2].day == today.day and _item[2].month == today.month:
                msg_parts.append(
                    f"•** {name}** `({code})` - **NA**\n")
            else:
                msg_parts.append(
                    f"• {name} `({code})` - NA\n")
        msg = "".join(msg_parts)

    await query_or_msg.reply_text(msg)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("GB"))
@loggers.async_log_access
@bot_auth.async_member_only
async def member_gb_ineligible(client: Client, query: CallbackQuery):
    await query.answer()
    result = db.get_gb_eligible_count()
    eligible = result[0][0]
    text = f"Eligible members: {eligible}\nQuorum (25%): {math.floor(eligible / 4)}"
    await _send_members_card(client, query.from_user.id, "General Body & quorum", [text], text)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("MC"))
@loggers.async_log_access
@bot_auth.async_member_only
async def get_MC(client: Client, query: CallbackQuery):
    await query.answer()
    await _send_members_list(client, query.from_user.id, "Management committee", [
        ("J022", "Secretary: Jacob Philip Kanianthara", ""),
        ("V019", "Lay Steward: Vibin Joseph Kuriakose", ""),
        ("M030", "Manu Joseph", ""),
        ("G006", "George Thomas", ""),
        ("S028", "Simon Philip", ""),
        ("S030", "Sam Varghese", ""),
        ("O001", "Vidya Oommen", ""),
        ("D017", "David Xie Han Keong", ""),
    ])

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("New Members Button"))
@loggers.async_log_access
@bot_auth.async_member_only
async def get_new_members(client: Client, query: CallbackQuery):
    await query.answer()
    members_list = db.get_new_members(months=12)
    rows = []
    for (family_name,) in members_list:
        # The CRM stores the family code as a trailing "(A001)" in fam_Name.
        match = re.fullmatch(r"(.+?)\s*\(([A-Za-z][0-9]{3})\)\s*", family_name)
        rows.append((match[2], match[1], "") if match else ("", family_name, ""))
    await _send_members_list(
        client, query.from_user.id, "New members 🆕", rows,
        subtitle="Last 12 months", empty="No new members",
    )