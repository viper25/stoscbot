from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from stoscbots.bot import keyboards
from dateutil import parser
import gspread

"""
Handle multiple callback queries data and return filter for each
"""


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data), data=data  # "data" kwarg is accessed with "flt.data" above
    )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Registrations for Service"))
@loggers.async_log_access
async def get_service_registrations(client: Client, query: CallbackQuery):
    await query.answer()
    _service_id = query.data.split(" ")[3]
    serviceName, serviceDate, serviceList, kids_count = db.get_members_for_serviceID(_service_id)
    msg = f"**{serviceName}** ({_service_id})\n`{serviceDate}`\n"
    msg += "➖➖➖➖➖➖➖\n\n"
    total = 0
    for _item in serviceList:
        # 33 is max char that shows on one line on mobile in this setting
        if len(f"`{_item[0]}:{_item[2]}` - {_item[1].strip()}") > 33:
            msg += f"`{_item[0]}: {_item[2]}`  {_item[1].strip()}"[:30] + "...\n"
        else:
            msg += f"`{_item[0]}: {_item[2]}`  {_item[1].strip()}\n"
        total += _item[2]
    msg += f"\n Families: **{len(serviceList)}**"
    msg += f"\n Kids < 12: **{kids_count[0][0]}** `(max)`"
    msg += f"\n Attendees: **{total}**"
    # Show this keyboard only to SMO
    if bot_auth.is_smo_member(query.from_user.id):
        await utils.edit_and_send_msg(query, msg, keyboards.get_services_keyboard(db.get_next_services()))
    else:
        utils.edit_and_send_msg(query, msg)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Prayer Requests"))
@loggers.async_log_access
# Check if there is any prayer request for this week submitted after current service starts at 7.45
async def get_prayer_requests(client: Client, query: CallbackQuery):
    await query.answer()
    await utils.edit_and_send_msg(query, "Please wait... ⌛", keyboards.get_services_keyboard(db.get_next_services()))

    # Credentials are at %APPDATA%\gspread\service_account.json or
    # ~/.config/gspread/service_account.json
    gc = gspread.service_account()
    sh = gc.open("Prayer Request (Responses)")
    list_requests = sh.sheet1.get_all_values()
    # Remove header
    list_requests.pop(0)
    start_of_week = utils.week_start_from_service_time()

    # Check if there is any prayer request for this week submitted after current service starts at 7.45
    prayer_requests_for_the_week = [
        _request for _request in list_requests if (parser.parse(_request[0]) - start_of_week).total_seconds() > 0
    ]
    departed_requests = [
        [_request[1], _request[2], _request[3]] for _request in prayer_requests_for_the_week if _request[3] != ""
    ]
    sick_requests = [[_request[1], _request[2], _request[4]] for _request in prayer_requests_for_the_week if _request[4] != ""]
    blessings_requests = [
        [_request[1], _request[2], _request[5]] for _request in prayer_requests_for_the_week if _request[5] != ""
    ]

    if prayer_requests_for_the_week:
        msg = f"**Prayer Requests**\n`since {start_of_week.strftime('%b %d, %H:%M %p')}`\n"
        msg += "➖➖➖➖➖➖➖➖\n"

        if departed_requests:
            msg += "\n--The Departed--"
            for _request in departed_requests:
                if "\n" in _request[2]:
                    for _line in _request[2].split("\n"):
                        msg += f"\n• {_line}"
                else:
                    # Only 1 name in the list
                    msg += f"\n• {_request[2]}"

        if sick_requests:
            msg += "\n\n--The Sick--"
            for _request in sick_requests:
                if "\n" in _request[2]:
                    for _line in _request[2].split("\n"):
                        msg += f"\n• {_line}"
                else:
                    # Only 1 name in the list
                    msg += f"\n• {_request[2]}"

        if blessings_requests:
            msg += "\n\n--Blessings--"
            for _request in blessings_requests:
                if "\n" in _request[2]:
                    for _line in _request[2].split("\n"):
                        msg += f"\n• {_line}"
                else:
                    # Only 1 name in the list
                    msg += f"\n• {_request[2]}"

        if len(msg) >= 4096:
            utils.edit_and_send_msg(
                query,
                "List too Long. Please check Google Sheet for full list.",
                keyboards.get_services_keyboard(db.get_next_services()),
            )
        else:
            await utils.edit_and_send_msg(query, msg, keyboards.get_services_keyboard(db.get_next_services()))
    else:
        await utils.edit_and_send_msg(query, "No Prayer Requests yet", keyboards.get_services_keyboard(db.get_next_services()))
