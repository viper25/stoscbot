import logging
import re
from typing import cast

from pyrogram import Client, enums, filters, types
from pyrogram.errors import RichMessageUnsupported
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup

from stoscbots.bot import family_profile, keyboards
from stoscbots.db import db
from stoscbots.util import bot_auth, loggers
from stoscbots.util.loggers import LOGLEVEL

logger = logging.getLogger("Handler.AreaPrayerGroups")
logger.setLevel(LOGLEVEL)


def _rich_text(value: str | list[str | types.RichText]) -> types.RichText:
    return cast(types.RichText, value)


def dynamic_data_filter(data: str) -> filters:
    """Create a filter that matches callback queries starting with the given data."""
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data),
        data=data,  # "data" kwarg is accessed with "flt.data" above
    )


def build_message(member_list, area_name):
    if not member_list:
        return "No members in this area"

    member_info = [
        f"• {member[0].split('(')[0]}`({member[0].split('(')[1][:4]})`"
        if "(" in member[0] else f"• {member[0]}"
        for member in member_list
    ]
    name = area_name[0][0] if area_name and area_name[0] else "this area"
    return f"**Members in {name}** `({len(member_list)})`\n\n" + \
        "\n".join(member_info)


async def _send_rich_prayer_group_card(
    client: Client, chat_id: int, rich: types.InputRichMessage, fallback: str,
    reply_markup: InlineKeyboardMarkup = keyboards.back_to_prayer_groups_keyboard,
) -> None:
    try:
        await client.send_rich_message(chat_id, rich, reply_markup=reply_markup)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich prayer group card; sending plain text")
        await client.send_message(
            chat_id, fallback, parse_mode=enums.ParseMode.DISABLED,
            reply_markup=reply_markup,
        )


@Client.on_callback_query(dynamic_data_filter("Area Prayer Group"))
@loggers.async_log_access
@bot_auth.async_member_only
async def get_area_prayer_group_members(client: Client, query: CallbackQuery):
    await query.answer()

    parts = query.data.split(" ")
    area = parts[3] if len(parts) > 3 else "1"
    member_list, area_name_result = db.get_members_for_area(area)

    area_name = area_name_result[0][0] if area_name_result and area_name_result[0] else f"Area {area}"
    fallback = build_message(member_list, [[area_name]])

    blocks: list[types.InputRichBlock] = [
        types.InputRichBlockSectionHeading(text=_rich_text(f"{area_name} 🤲🏻"), size=3),
    ]

    if not member_list:
        blocks.append(types.InputRichBlockParagraph(
            text=_rich_text("No members registered in this area.")
        ))
    else:
        count = len(member_list)
        subtitle = f"{count} {'families' if count != 1 else 'family'}"
        blocks.append(types.InputRichBlockParagraph(text=_rich_text(subtitle)))

        cells = [[
            types.RichBlockTableCell(text=_rich_text("Family"), is_header=True),
        ]]
        for row in member_list:
            fam_str = row[0] if isinstance(row, (tuple, list)) else str(row)
            match = re.fullmatch(r"(.+?)\s*\(([A-Za-z0-9]+)\)\s*", fam_str)
            if match:
                name, code = match.group(1).strip(), match.group(2).strip()
                cell_content = cast(types.RichText, [name, " (", family_profile.family_code_link(code), ")"])
            else:
                cell_content = cast(types.RichText, fam_str)
            cells.append([types.RichBlockTableCell(text=cell_content)])

        blocks.append(types.InputRichBlockTable(cells=cells, is_striped=True, is_compact=True))
        blocks.append(types.InputRichBlockFooter(
            text=_rich_text("Tap a family code to view their profile.")
        ))

    await _send_rich_prayer_group_card(
        client, query.from_user.id, types.InputRichMessage(blocks=blocks), fallback,
    )
