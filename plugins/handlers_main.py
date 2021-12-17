from pyrogram import Client, filters
from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from datetime import datetime
import re

# ==================================================
# Command Handlers
@Client.on_message(filters.command(["start"]))
@loggers.log_access
@bot_auth.member_only
def start_handler(client, message):
    msg="What would you like to do?\n Select an option:"
    message.reply(msg, reply_markup=keyboards.get_main_keyboard(message.from_user.id))
# -------------------------------------------------
@Client.on_message(filters.command(["help"]))
@loggers.log_access
@bot_auth.member_only
def help_handler(client, message):
    msg="**Help**\n➖➖"
    msg+="\nI can help you use STOSC Bot. If you're new to the Bot, please see /help\n"
    msg+="\nYou can control me by sending these commands or clicking the buttons at /start:\n"
    msg+="\n/help - Show this help message"
    msg+="\n/start - Start the bot\n"
    msg+="\n** The below commands are restricted use:**\n"
    msg+="\n/u [member code or name] - Search for a member by member code or Name"
    msg+="\n/x [member code] - Show member contributions"
    msg+="\n/xs [member code] - Show member subscriptions"
    msg+="\n/year [year in YYYY] - Show members born on this year"
    message.reply(msg, reply_markup=keyboards.back_to_main_keyboard)
# -------------------------------------------------
@Client.on_message(filters.command(["year"]))
@loggers.log_access
@bot_auth.management_only
def year_handler(client, message):
    if len(message.command)==1:
        msg="Please enter the year you want to view\ne.g. '/year 2020'"
        message.reply(msg, reply_markup=keyboards.back_to_main_keyboard)
        return
    year = message.command[1]
    if (len(year) ==4 and (re.match('\d{4}', year) is not None)):
        result=db.get_members_born_on(year)
        msg = f"**Members Born on {year}** ({len(result)})\n➖➖➖➖➖➖➖➖"
        if result:
            for member in result:
                msg+=f"\n**{member[0]}**\n"
                msg+=f"({member[1]})\n"
                msg+=f"{member[2]}\n"
                msg += f"{member[3]}\n" if (member[3] != "" and member[3] is not None) else ""
                msg += f"{member[4]}\n" if (member[4] != "" and member[4] is not None) else ""
                msg += f"{member[5]}\n" if (member[2] != "" and member[5] is not None) else ""
            message.reply(msg, reply_markup=keyboards.back_to_main_keyboard)
        else:
            msg = f"No members born on {year}"
            message.reply(msg)
    else:
        msg="Please enter a valid 4 digit year to search"
        message.reply(msg,quote=True)
# -------------------------------------------------
# Command Handlers
@Client.on_message(filters.command(["u"]))
@loggers.log_access
@bot_auth.area_prayer_coordinator_only
def member_search_cmd_handler(client, message):
    if len(message.command) != 2:
        msg="Please enter a Member Code or Name to search"
        message.reply(msg,quote=True)
        return
    # Match member codes such as V019. One char followed by 2 or 3 digits
    if utils.is_valid_member_code(message.command[1]) is not None:
        #A member code has been sent
        result=db.get_member_details(message.command[1],'code')
        if len(result) == 0:
            message.reply("No such Member", quote=True)
            return
        elif len(result) >= 1:  
            msg = utils.generate_profile_msg(result)   
            utils.send_profile_address_and_pic(client, message, msg,result)
    else:
        # A search string and not member code
        result=db.get_member_details(message.command[1],'free_text')
        if not result or len(result) == 0:
            message.reply("No such Member", quote=True)
        elif len(result) >= 1:
            msg = f'🔎 Search results for "`{message.command[1]}`"\n--------------------------------------------'
            msg += '`\n⚡ = Head of Family`'
            msg += '`\n👦🏻 = Boy   👧🏻 = Girl`'
            msg += '`\n🧔🏻 = Man   👩🏻 = Woman`'
            message.reply(msg,reply_markup=keyboards.get_member_listing_keyboard(result))
        
# ==================================================
'''
Handle multiple callback queries data and return filter for each
'''
def dynamic_data_filter1(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data  # "data" kwarg is accessed with "flt.data" above
    )
def dynamic_data_filter2(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data),
        data=data  # "data" kwarg is accessed with "flt.data" above
    )
# ==================================================
# Callback Handlers (for Buttons)
@Client.on_callback_query(dynamic_data_filter1("Main Menu"))
@loggers.log_access
def show_main_menu(client, query):
    query.answer()
    msg = "➖➖**Main Menu**➖➖"
    query.message.reply(msg, reply_markup=keyboards.get_main_keyboard(query.from_user.id))
# -------------------------------------------------
# Callback Handlers (for Buttons)
@Client.on_callback_query(dynamic_data_filter1("Services Menu"))
@loggers.log_access
def show_services_menu(client, query):
    query.answer()
    result=db.get_next_services()
    if len(result) == 0:
        msg="No Services"
    else:
        msg="**Upcoming Services**\n➖➖➖➖➖➖➖\n\n"
        _counter=0
        # Get first group in result set and see if it changes
        group=result[0][5]
        msg += f"**--Group {group}--**\n"
        for _item in result:
            if group==_item[5]:
                _counter += 1
                # Assign current group
                group=_item[5]
                if datetime.now() > _item[2]:
                    # Strikethrough finished services
                    msg += f'~~{_counter}. {_item[1]} on {_item[2].strftime("%b %d %I:%M %p")}~~ `({_item[4]}/{_item[3]})`\n'
                else:
                    msg += f'{_counter}. {_item[1]} on {_item[2].strftime("%b %d %I:%M %p")} `({_item[4]}/{_item[3]})`\n'
            else:
                # A new group, so reset number and draw a line
                _counter=1
                group=_item[5]
                msg += f"\n**--Group {group}--**\n"
                if datetime.now() > _item[2]:
                    # Strikethrough finished services
                    msg += f'~~{_item[1]} on {_item[2].strftime("%b %d %I:%M %p")}~~ `({_item[4]}/{_item[3]})`\n'
                else:
                    msg += f'{_counter}. {_item[1]} on {_item[2].strftime("%b %d %I:%M %p")} `({_item[4]}/{_item[3]})`\n'
    # Show this keyboard only to SMO
    if bot_auth.is_smo_member(query.from_user.id):
        utils.edit_and_send_msg(query, msg, keyboards.get_services_keyboard(db.get_next_services()))
    else:
        utils.edit_and_send_msg(query, msg, keyboards.back_to_main_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Members Menu"))
@loggers.log_access
def show_members_menu(client, query):
    query.answer()
    msg = "➖➖**Members Menu**➖➖"
    utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Prayer Groups Menu"))
@loggers.log_access
def show_prayer_groups_menu(client, query):
    query.answer()
    msg = "➖➖**Area Prayer Group Menu**➖➖"
    utils.edit_and_send_msg(query, msg, keyboards.area_prayer_groups_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Finance Menu"))
@loggers.log_access
def show_finance_menu(client, query):
    query.answer()
    msg = "➖➖**Finance Menu**➖➖"
    query.message.reply(msg, reply_markup=keyboards.finance_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("My Details Menu"))
@loggers.log_access
def show_my_details_menu(client, query):
    query.answer()
    msg = "➖➖**My Details Menu**➖➖"
    utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("My Harvest Festival Menu"))
@loggers.log_access
def show_my_harvest_festival_menu(client, query):
    query.answer()
    member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    msg = "➖➖**My Harvest Details Menu** 🌽➖➖"
    my_auction_link = f"`My Auction Link:` {utils.get_member_auction_link(member_code)}"
    my_auction_spend = utils.generate_msg_member_auction_purchases(member_code)
    msg += "\n\n" + my_auction_spend
    msg += "\n" + my_auction_link
    utils.edit_and_send_msg(query, msg, keyboards.back_to_main_keyboard)
# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("PayNow Menu"))
@loggers.log_access
def show_paynow_menu(client, query):
    query.answer()
    msg = "**Payment Options**\n"
    msg += "➖➖➖➖➖➖\n"
    msg += "You may pay by one of these ways:\n"
    msg += "    • PayNow to UEN: **S79SS0001L**\n"
    msg += "    • PayNow to QR code shown above\n"
    msg += "    • Bank transfer to DBS: **0480155596**\n"
    msg += "    • NETS, Cash or Cheque (payable to `St. Thomas Orthodox Syrian Cathedral`) at the church office\n"
    msg += "\n`Please mention your family code and purpose of contribution.`\n"
    msg += "`For multiple payments, you can make one transfer and email the breakdown to` accounts@stosc.com"
    client.send_photo(chat_id=query.from_user.id, photo='https://stosc.com/paynow/img/QR.png',caption=msg,reply_markup = keyboards.back_to_main_keyboard)
# --------------------------------------------------
# Handler for buttons generated from /u MyName search command 
@Client.on_callback_query(dynamic_data_filter2("Member_"))
@loggers.log_access
def member_search_button_handler(client, query):
    query.answer()
    _member_code=query.data.split('_')[1]
    result=db.get_member_details(_member_code,'code')
    msg = utils.generate_profile_msg(result)
    utils.send_profile_address_and_pic(client, query, msg,result)