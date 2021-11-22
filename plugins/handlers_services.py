from pyrogram import Client, filters
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from stoscbots.bot import keyboards
# ==================================================
'''
Handle multiple callback queries data and return filter for each
'''
def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data),
        data=data  # "data" kwarg is accessed with "flt.data" above
    )

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Registrations for Service"))
@loggers.log_access
def get_service_registrations(client, query):
    query.answer()
    _service_id = query.data.split(' ')[3]
    serviceName, serviceDate, serviceList, kids_count=db.get_members_for_serviceID(_service_id)
    msg=f"**{serviceName}** ({_service_id})\n`{serviceDate}`\n"
    msg += "➖➖➖➖➖➖➖\n\n"
    total=0
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
        utils.edit_and_send_msg(query, msg, keyboards.get_services_keyboard(db.getNextServices()))
    else:
        utils.edit_and_send_msg(query, msg)