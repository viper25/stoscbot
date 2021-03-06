from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.util import loggers, utils
from stoscbots.bot import keyboards
# ==================================================
'''
Handle multiple callback queries data and return filter for each
'''
def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data  # "data" kwarg is accessed with "flt.data" above
    )
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter("St. Marys Project Summary Button"))
@loggers.async_log_access
async def get_finance_stmarys_executive_summary(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "**EXECUTIVE SUMMARY**\n"
    msg += "➖➖➖➖➖➖➖➖➖\n\n"
    report = utils.get_tracked_projects(raw_data=True)
    for _item in report:
        if _item['AccountName'] == 'Snehasparsham' and _item['Total']:
            msg += f"•** {_item['AccountName']}** - `${_item['Total']:,.2f}`\n"
        elif _item['AccountName'] == 'Vanitha Dinam' and _item['Total']:
            msg += f"•** {_item['AccountName']}** - `${_item['Total']:,.2f}`\n"
        elif _item['AccountName'] == 'Pethrutha' and _item['Total']:
            msg += f"•** {_item['AccountName']}** - `${_item['Total']:,.2f}`\n"
        elif _item['AccountName'] == 'Migrant Workers' and _item['Total']:
            msg += f"•** {_item['AccountName']}** - `${_item['Total']:,.2f}`\n"
    await utils.edit_and_send_msg(query, msg, keyboards.stmarys_menu_keyboard)
