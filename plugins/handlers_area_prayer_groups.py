from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils


def dynamic_data_filter(data: str) -> filters:
    """Create a filter that matches callback queries starting with the given data."""
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data),
        data=data  # "data" kwarg is accessed with "flt.data" above
    )


def build_message(member_list, area_name):
    if not member_list:
        return "No members in this area"

    member_info = [
        f"• {member[0].split('(')[0]}`({member[0].split('(')[1][:4]})`"
        for member in member_list
    ]
    return f"**Members in {area_name[0][0]}** `({len(member_list)})`\n\n" + \
        "\n".join(member_info)


@Client.on_callback_query(dynamic_data_filter("Area Prayer Group"))
@loggers.async_log_access
async def get_area_prayer_group_members(client: Client, query: CallbackQuery):
    await query.answer()

    area = query.data.split(' ')[3]
    member_list, area_name = db.get_members_for_area(area)

    msg = build_message(member_list, area_name)
    await utils.edit_and_send_msg(query, msg, keyboards.area_prayer_groups_keyboard)
