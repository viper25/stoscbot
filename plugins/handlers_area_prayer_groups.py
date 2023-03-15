import random
import string
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.db import db
from stoscbots.util import loggers
from stoscbots.bot import keyboards
from stoscbots.util import utils
from faker import Faker

fake = Faker()
def generate_random_memberID():
    # Choose a random character
    char = random.choice(string.ascii_uppercase)
    # Choose 3 random digits
    digits = "".join(random.choices(string.digits, k=3))
    # Concatenate the character and digits
    return char + digits


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
@loggers.async_log_access
async def get_area_prayer_group_members(client: Client, query: CallbackQuery):
    await query.answer()
    _area = query.data.split(' ')[3]
    _memberlist,area_name=db.get_members_for_area(_area)
    if len(_memberlist) ==0:
        msg="No members in this area"
    else:
        msg=f"**Members in {area_name[0][0]}** `({len(_memberlist)})` \n\n"
        for _member in _memberlist:
            msg += f"• {fake.name()} `({generate_random_memberID()})`\n"
    await utils.edit_and_send_msg(query, msg, keyboards.area_prayer_groups_keyboard)