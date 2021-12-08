from pyrogram import Client, filters
from stoscbots.db import db
from stoscbots.util import loggers
from stoscbots.bot import keyboards
from stoscbots.util import utils

'''
Handle multiple callback queries data and return filter for each
'''
def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data),
        data=data  # "data" kwarg is accessed with "flt.data" above
    )

# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("Area Prayer Group"))
@loggers.log_access
def get_area_prayer_group_members(client, query):
    query.answer()
    _area = query.data.split(' ')[3]
    _memberlist,area_name=db.get_members_for_area(_area)
    if len(_memberlist) ==0:
        msg="No members in this area"
    else:
        msg=f"**Members in {area_name[0][0]}** `({len(_memberlist)})` \n\n"
        for _member in _memberlist:
            msg += f"• {_member[0].split('(')[0]}`({_member[0].split('(')[1][:4]})`\n"
    utils.edit_and_send_msg(query, msg, keyboards.area_prayer_groups_keyboard)