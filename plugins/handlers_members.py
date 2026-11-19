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
from stoscbots.util import bot_auth, loggers
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


async def _send_rich_members_card(
    client: Client, chat_id: int, rich: types.InputRichMessage, fallback: str,
) -> None:
    try:
        await client.send_rich_message(chat_id, rich, reply_markup=keyboards.back_to_members_keyboard)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich Members card; sending plain text")
        await client.send_message(
            chat_id, fallback, parse_mode=enums.ParseMode.DISABLED,
            reply_markup=keyboards.back_to_members_keyboard,
        )


type TableValue = str | tuple[str, types.RichText] | None


def _family_table_value(name: str, code: str) -> TableValue:
    name, code = name.strip(), code.strip()
    if not code:
        return name
    return f"{name} ({code})", cast(types.RichText, [name, " (", family_profile.family_code_link(code), ")"])


async def _send_members_table(
    client: Client, chat_id: int, heading: str, headers: tuple[str, ...],
    rows: Iterable[tuple[TableValue, ...]], *, subtitle: str = "",
    empty: str = "No results", right_align_last: bool = False, missing_note: str = "",
) -> None:
    """Render compact table cells with separate plain text for rich values."""
    blocks: list[types.InputRichBlock] = [
        types.InputRichBlockSectionHeading(text=cast(types.RichText, heading), size=3),
    ]
    fallback = [heading]
    if subtitle:
        blocks.append(types.InputRichBlockParagraph(text=cast(types.RichText, subtitle)))
        fallback.append(subtitle)
    fallback.append("")
    cells = [[
        types.RichBlockTableCell(text=cast(types.RichText, label), is_header=True)
        for label in headers
    ]]
    has_missing = False
    for row in rows:
        rich_row = []
        plain_row = []
        for column, value in enumerate(row):
            if value is None:
                plain = "—"
                rich = cast(types.RichText, plain)
                if missing_note:
                    rich = types.RichTextReferenceLink(
                        text=cast(types.RichText, "—¹"), reference_name="missing-year",
                    )
                    has_missing = True
            elif isinstance(value, tuple):
                plain, rich = value
            else:
                plain, rich = value, cast(types.RichText, value)
            rich_row.append(types.RichBlockTableCell(
                text=rich, align="right" if right_align_last and column == len(headers) - 1 else None,
            ))
            plain_row.append(plain)
        cells.append(rich_row)
        fallback.append("• " + " · ".join(plain_row))

    if len(cells) == 1:
        blocks.append(types.InputRichBlockParagraph(text=cast(types.RichText, empty)))
        fallback.append(empty)
    else:
        if has_missing:
            blocks.append(types.InputRichBlockAnchor(name="members-table"))
        blocks.append(types.InputRichBlockTable(cells=cells, is_striped=True, is_compact=True))
        if has_missing:
            note = f"¹ {missing_note}"
            blocks.append(types.InputRichBlockFooter(text=cast(types.RichText, [
                types.RichTextReference(text=cast(types.RichText, note), name="missing-year"),
                "  ",
                types.RichTextAnchorLink(text=cast(types.RichText, "↑ Back to table"), anchor_name="members-table"),
            ])))
            fallback.extend(["", note])
    await _send_rich_members_card(client, chat_id, types.InputRichMessage(blocks=blocks), "\n".join(fallback))


def _birthday_age(birthday: str, current_year: int) -> str:
    parts = birthday.split("/")
    year = int(parts[2]) if len(parts) == 3 and parts[2].isdecimal() else 0
    return str(current_year - year) if 0 < year <= current_year else "NA"


def _birthday_table_date(birthday: str, today: date) -> TableValue:
    try:
        day, month, *_ = birthday.split("/")
        # Use a leap year so 29 February can be displayed without the birth year.
        birthday_date = date(2000, int(month), int(day))
    except ValueError:
        logger.warning("Cannot format day and month for a weekly birthday")
        return "—"
    label = f"{birthday_date.day} {birthday_date:%b}"
    if (birthday_date.month, birthday_date.day) == (today.month, today.day):
        return label, types.RichTextMarked(text=cast(types.RichText, label))
    return label


async def _send_weekly_anniversary_card(
    client: Client, chat_id: int, week: str, rows: Iterable[tuple[str, str, date]], today: date,
) -> None:
    heading = "Wedding anniversaries this week 💍"
    fallback = [heading, week, ""]
    blocks: list[types.InputRichBlock] = [
        types.InputRichBlockSectionHeading(text=cast(types.RichText, heading), size=3),
        types.InputRichBlockParagraph(text=cast(types.RichText, week)),
    ]
    cells = [[
        types.RichBlockTableCell(text=cast(types.RichText, label), is_header=True)
        for label in ("Date", "Couple", "Years")
    ]]
    missing_year = False
    for code, name, wedding in rows:
        day = f"{wedding.day} {wedding:%b}"
        is_today = (wedding.month, wedding.day) == (today.month, today.day)
        date_cell = cast(types.RichText, day)
        if is_today:
            date_cell = types.RichTextMarked(text=date_cell)

        name, code = name.strip(), code.strip()
        couple: list[str | types.RichText] = [name]
        if code:
            couple.extend([" (", family_profile.family_code_link(code), ")"])
        if wedding.year != 1900 and wedding.year <= today.year:
            years = str(today.year - wedding.year)
            year_cell = cast(types.RichText, years)
        else:
            missing_year = True
            years = "—"
            year_cell = types.RichTextReferenceLink(
                text=cast(types.RichText, "—¹"), reference_name="missing-year",
            )
        cells.append([
            types.RichBlockTableCell(text=date_cell),
            types.RichBlockTableCell(text=cast(types.RichText, couple)),
            types.RichBlockTableCell(text=year_cell, align="right"),
        ])
        label = f"{name} ({code})" if code else name
        fallback.append(f"• {day} · {label} · {years}")

    if len(cells) == 1:
        empty = "No wedding anniversaries this week"
        blocks.append(types.InputRichBlockParagraph(text=cast(types.RichText, empty)))
        fallback.append(empty)
    else:
        if missing_year:
            blocks.append(types.InputRichBlockAnchor(name="anniversary-table"))
        blocks.append(types.InputRichBlockTable(cells=cells, is_striped=True, is_compact=True))
        if missing_year:
            note = "¹ The wedding year is not available."
            blocks.append(types.InputRichBlockFooter(text=cast(types.RichText, [
                types.RichTextReference(text=cast(types.RichText, note), name="missing-year"),
                "  ",
                types.RichTextAnchorLink(text=cast(types.RichText, "↑ Back to table"), anchor_name="anniversary-table"),
            ])))
            fallback.extend(["", note])

    await _send_rich_members_card(client, chat_id, types.InputRichMessage(blocks=blocks), "\n".join(fallback))


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Member Birthday Today Button"))
@loggers.async_log_access
@bot_auth.async_member_only
async def get_today_bdays(client: Client, query: CallbackQuery):
    await query.answer()
    _, _, result = db.get_bday('d')
    current_year = date.today().year
    rows = ((_family_table_value(name, code), _birthday_age(birthday, current_year))
            for code, name, birthday, _ in result)
    await _send_members_table(
        client, query.from_user.id, "Birthdays today 🎂", ("Member", "Age"), rows,
        empty="No birthdays today", right_align_last=True,
    )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Member Anniversary Today Button"))
@loggers.async_log_access
@bot_auth.async_member_only
async def get_today_anniversaries(client: Client, query: CallbackQuery):
    await query.answer()
    _, _, result = db.get_anniversaries('d')
    current_year = date.today().year
    rows = (
        (_family_table_value(name, code),
         str(current_year - wedding.year) if wedding.year != 1900 and wedding.year <= current_year else None)
        for code, name, wedding in result
    )
    await _send_members_table(
        client, query.from_user.id, "Wedding anniversaries today 💍", ("Couple", "Years"), rows,
        empty="No wedding anniversaries today", right_align_last=True, missing_note="The wedding year is not available.",
    )


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
        today = date.today()
        rows = (
            (_birthday_table_date(birthday, today), _family_table_value(name, code), _birthday_age(birthday, today.year))
            for code, name, birthday, _ in result
        )
        await _send_members_table(
            client, query_or_msg.from_user.id, "Birthdays this week 🎂", ("Date", "Member", "Age"), rows,
            subtitle=f"{start} – {end}", empty="No birthdays this week",
            right_align_last=True,
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
        await _send_weekly_anniversary_card(
            client, query_or_msg.from_user.id, f"{start} – {end}", result, today,
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
    await _send_members_table(
        client, query.from_user.id, "General Body & quorum", ("Measure", "Count"),
        [("Eligible members", str(eligible)), ("Quorum (25%)", str(math.floor(eligible / 4)))],
        right_align_last=True,
    )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("MC"))
@loggers.async_log_access
@bot_auth.async_member_only
async def get_MC(client: Client, query: CallbackQuery):
    await query.answer()
    roster = [
        ("Secretary", "Jacob Philip Kanianthara", "J022"),
        ("Lay Steward", "Vibin Joseph Kuriakose", "V019"),
        ("Committee member", "Manu Joseph", "M030"),
        ("Committee member", "George Thomas", "G006"),
        ("Committee member", "Simon Philip", "S028"),
        ("Committee member", "Sam Varghese", "S030"),
        ("Committee member", "Vidya Oommen", "O001"),
        ("Committee member", "David Xie Han Keong", "D017"),
    ]
    await _send_members_table(
        client, query.from_user.id, "Management committee", ("Role", "Member"),
        ((role, _family_table_value(name, code)) for role, name, code in roster),
    )

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
        rows.append((_family_table_value(match[1], match[2]) if match else family_name,))
    await _send_members_table(
        client, query.from_user.id, "New members 🆕", ("Family",), rows,
        subtitle="Last 12 months", empty="No new members",
    )