import os
import asyncio
import logging
from stoscbots.util.loggers import LOGLEVEL
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from stoscbots.bot import keyboards
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from datetime import datetime

# Module logger
logger = logging.getLogger('Handler.Main')
logger.setLevel(LOGLEVEL)
VIBIN_TELEGRAM_ID = int(os.environ.get('VIBIN_TELEGRAM_ID'))

# ==================================================
# Command Handlers
@Client.on_message(filters.command(["start","hi","hello"]) & filters.private)
@loggers.async_log_access
async def start_handler(client: Client, message: Message):
    email = None
    member_code = None
    # Check if user is authorized
    if not bot_auth.is_member(message.from_user.id):
        unauth_msg=f"Unauthorized Access by **[{message.from_user.id}:{message.from_user.username}:{message.from_user.first_name}]**\nCmd `/start`"
        await client.send_message(chat_id=VIBIN_TELEGRAM_ID,text=unauth_msg)
        # Start a conversation with the user to ask for Member Code and Email
        await client.send_sticker(chat_id=message.from_user.id, sticker='CAACAgIAAxkBAAIFJV-X6UKaAAEDx4Nqup6acSBW6DlThgACoAMAAvoLtgj5yjtMiAXK4hsE')
        await message.reply_text("**You are not authorized to use this bot**\nHowever, if you are a STOSC member, do provide your details for access.\n\n`Enter your member code:`", disable_web_page_preview=True)
        try:
            member_code = await client.listen.Message(filters.text, id = filters.user(message.from_user.id), timeout = 30)
            logger.info(f"Unauthorized Member Request Code: {member_code.text}")
            if not utils.is_valid_member_code(member_code.text):
                await message.reply_text("👎🏼 Invalid member code. Please try again: /start")
                # Cancel the conversation
                await client.listen.Cancel(filters.user(message.from_user.id))
                return
        except asyncio.TimeoutError:
            await message.reply('Timed out, do type /start again')
            return
        if member_code and member_code.text == '/start':
            # Cancel the conversaion
            await client.listen.Cancel(filters.user(message.from_user.id))
            return
        await message.reply_text("`Enter your email:`")
        try:
            email = await client.listen.Message(filters.text, id = filters.user(message.from_user.id), timeout = 30)
            logger.info(f"Unauthorized Member Request Email: {email.text}")
            #  Check if email is valid
            if not utils.is_valid_email(email.text):
                await message.reply_text("👎🏼 Invalid email. Please try again: /start")
                # Cancel the conversaion
                await client.listen.Cancel(filters.user(message.from_user.id))
                return
        except asyncio.TimeoutError:
            await message.reply('Timed out, do type /start again')
            return
        if email and email.text == '/start':
            # Cancel the conversaion
            await client.listen.Cancel(filters.user(message.from_user.id))
            return
        if member_code and email:
            await message.reply_text(f"I'll inform the Managing Committee of your request. Once your ID is verified, they shall add you for access to the Bot.\n\n**Details submitted:**\n`Member Code: {member_code.text}\nEmail: {email.text}`")
            # Send Telegram message to Managing Committee
            await client.send_message(chat_id=VIBIN_TELEGRAM_ID,text=f"New member request:\nMember Code: `{member_code.text}`\nEmail: `{email.text}`\nTelegram ID: `{message.from_user.id}`")
        else:
            await message.reply_text("Sorry try again")
    else:
        msg = "What would you like to do?\n Select an option:"
        await message.reply_text(msg, reply_markup=keyboards.get_main_keyboard(message.from_user.id))

# -------------------------------------------------
@Client.on_message(filters.command(["help"]))
@loggers.async_log_access
@bot_auth.async_member_only
async def help_handler(client: Client, message: Message):
    msg = "**Help**\n➖➖"
    msg += "\nWatch this [YouTube video](https://youtu.be/67FAw0buXIA) to see bot the STOSC Bot works 🤖\n"
    msg += "\nYou can control me by sending these commands or clicking the buttons at /start:\n"
    msg += "\n• /help - Show this help message"
    msg += "\n• /start - Start the bot"
    msg += "\n• /u [member code or name] - Search for a member by member code or Name e.g. `/u A001`"
    msg += "\n• /year [year in YYYY] - Show members born on this year e.g. `/year 1976`\n"
    msg += "\n** 🚫 The below commands are for the management committee only: 🚫**\n"
    msg += "\n• /x [member code] - Show member contributions"
    msg += "\n• /xs [member code] - Show member subscriptions"
    msg += "\n• /version or /ver - Show bot version"
    msg += "\n• /bday  - Show this week's bday list without age"
    msg += "\n• /anniv  - Show this week's anniversary list without years"
    await message.reply_text(msg, reply_markup=keyboards.back_to_main_keyboard, disable_web_page_preview=True)


# -------------------------------------------------
@Client.on_message(filters.command(["year"]))
@loggers.async_log_access
async def year_handler(client: Client, message: Message):
    if len(message.command) == 1:
        msg = "Please enter the year you want to view\ne.g. '/year 2020'"
        await message.reply_text(msg, reply_markup=keyboards.back_to_main_keyboard)
        return
    year = message.command[1]
    if utils.is_valid_year(year):
        result = db.get_members_born_on(year)
        msg = f"**Members Born on {year}** ({len(result)})\n➖➖➖➖➖➖➖➖"
        if result:
            for member in result:
                msg += f"\n**{member[0]}**\n"
                msg += f"({member[1]})\n"
                msg += f"{member[2]}\n"
                msg += f"{member[3]}\n" if (member[3] != "" and member[3] is not None) else ""
                msg += f"{member[4]}\n" if (member[4] != "" and member[4] is not None) else ""
                msg += f"{member[5]}\n" if (member[2] != "" and member[5] is not None) else ""
            await message.reply_text(msg, reply_markup=keyboards.back_to_main_keyboard)
        else:
            msg = f"No members born on {year}"
            await message.reply_text(msg)
    else:
        msg = "Please enter a valid 4 digit year to search"
        await message.reply_text(msg, quote=True)


# -------------------------------------------------
# Command Handlers
@Client.on_message(filters.command(["u"]))
@loggers.async_log_access
@bot_auth.async_member_only
async def member_search_cmd_handler(client: Client, message: Message):
    if len(message.command) != 2:
        msg = "Please enter a Member Code or Name to search\n e.g. `/u A001`"
        await message.reply_text(msg, quote=True)
        return
    # Match member codes such as V019. One char followed by 2 or 3 digits
    if utils.is_valid_member_code(message.command[1]):
        # A member code has been sent
        result = db.get_member_details(message.command[1], "code")
        if len(result) == 0:
            await message.reply_text("No such Member", quote=True)
            return
        elif len(result) >= 1:
            msg = utils.generate_profile_msg_for_family(result)
            await utils.send_profile_address_and_pic(
                client, message, msg, result, searched_person=None, searched_person_name=None
            )
    else:
        # A search string and not member code
        result = db.get_member_details(message.command[1], "free_text")
        if not result or len(result) == 0:
            await message.reply_text("No such Member", quote=True)
        elif len(result) >= 1:
            msg = f"🔎 Search results for `{message.command[1]}`\n"
            msg += "➖➖➖➖➖➖➖➖➖➖➖"
            msg += "`\n⚡ = Head of Family`"
            msg += "`\n👦🏻 = Boy   👧🏻 = Girl`"
            msg += "`\n🧔🏻 = Man   👩🏻 = Woman`"
            await message.reply_text(msg, reply_markup=keyboards.get_member_listing_keyboard(result))


# ==================================================
"""
Handle multiple callback queries data and return filter for each
"""


def dynamic_data_filter1(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data, data=data  # "data" kwarg is accessed with "flt.data" above
    )


def dynamic_data_filter2(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data), data=data  # "data" kwarg is accessed with "flt.data" above
    )


# ==================================================
# Callback Handlers (for Buttons)
@Client.on_callback_query(dynamic_data_filter1("Main Menu"))
@loggers.async_log_access
async def show_main_menu(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "➖➖**Main Menu**➖➖"
    await query.message.reply_text(msg, reply_markup=keyboards.get_main_keyboard(query.from_user.id))


# -------------------------------------------------
# Callback Handlers (for Buttons)
@Client.on_callback_query(dynamic_data_filter1("Services Menu"))
@loggers.async_log_access
async def show_services_menu(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "➖➖**Services Menu**➖➖\n"
    await utils.edit_and_send_msg(query, msg, keyboards.get_services_keyboard())


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Members Menu"))
@loggers.async_log_access
async def show_members_menu(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "➖➖**Members Menu**➖➖"
    await utils.edit_and_send_msg(query, msg, keyboards.members_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Prayer Groups Menu"))
@loggers.async_log_access
async def show_prayer_groups_menu(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "➖➖**Area Prayer Group Menu**➖➖"
    await utils.edit_and_send_msg(query, msg, keyboards.area_prayer_groups_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Finance Menu"))
@loggers.async_log_access
async def show_finance_menu(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "➖➖**Finance Menu**➖➖"
    await query.message.reply_text(msg, reply_markup=keyboards.finance_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("St. Marys Menu"))
@loggers.async_log_access
async def show_st_marys_menu(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "➖➖**St. Mary's Menu**➖➖"
    await query.message.reply_text(msg, reply_markup=keyboards.stmarys_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("My Details Menu"))
@loggers.async_log_access
async def show_my_details_menu(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "➖➖**My Details Menu**➖➖"
    await utils.edit_and_send_msg(query, msg, keyboards.my_details_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("My Harvest Festival Menu"))
@loggers.async_log_access
async def show_my_harvest_festival_menu(client: Client, query: CallbackQuery):
    await query.answer()
    member_code = utils.getMemberCode_from_TelegramID(query.from_user.id)
    msg = "➖➖**🌽 My Harvest Details Menu** 🌽➖➖"
    msg += "\n`Your activity from the Harvest Festival`"
    my_auction_spend = utils.generate_msg_member_auction_purchases(member_code)
    msg += "\n\n" + my_auction_spend
    my_auction_contrib = utils.generate_msg_member_auction_contributions(member_code)
    if my_auction_contrib:
        msg += "\n\n" + my_auction_contrib
    # my_auction_link = utils.get_member_auction_link(member_code)
    # if my_auction_link:
    #     msg += "\n\n" + f"——————\n▪️ Auction Link: {my_auction_link}\n"
    #     # msg += "\n" + f"▪️ Zoom Link: https://us06web.zoom.us/j/81149591863?pwd=V2V2cnE0SWxGNVM2SGlha0VJVk5TZz09"
    await utils.edit_and_send_msg(query, msg, keyboards.harvest_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("PayNow Menu"))
@loggers.async_log_access
async def show_paynow_menu(client: Client, query: CallbackQuery):
    await query.answer()
    msg = "**Payment Options**\n"
    msg += "➖➖➖➖➖➖\n"
    msg += "You may pay by one of these ways:\n"
    msg += "    • PayNow to UEN: **S79SS0001L**\n"
    msg += "    • PayNow to QR code shown above\n"
    msg += "    • Bank transfer to DBS: **0480155596**\n"
    msg += "    • NETS, Cash or Cheque (payable to `St. Thomas Orthodox Syrian Cathedral`) at the church office\n"
    msg += "\n`Please mention your family code and purpose of contribution.`\n"
    msg += "`For multiple payments, you can make one transfer and email the breakdown to` accounts@stosc.com"
    await client.send_photo(
        chat_id=query.from_user.id,
        photo="https://stosc.com/paynow/img/QR.png",
        caption=msg,
        reply_markup=keyboards.back_to_main_keyboard,
    )


# --------------------------------------------------
# Handler for buttons generated from /u MyName search command
@Client.on_callback_query(dynamic_data_filter2("Member_"))
@loggers.async_log_access
async def member_search_button_handler(client: Client, query: CallbackQuery):
    await query.answer()
    _member_code = query.data.split("_")[1]
    person_ID = query.data.split("_")[2]
    result = db.get_member_details(_member_code, "code")
    msg = utils.generate_profile_msg_for_family(result)
    await utils.send_profile_address_and_pic(
        client, query, msg, result, query.data.split("_")[2], db.get_person_name(person_ID)[0][0]
    )
