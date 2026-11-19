import asyncio
import logging

import aiofiles
from pyrogram import Client, errors, filters
from pyrogram.errors import BadRequest, RichMessageUnsupported
from pyrogram.types import CallbackQuery, LinkPreviewOptions, Message

from stoscbots.bot import family_profile, keyboards
from stoscbots.db import db
from stoscbots.util import bot_auth, loggers, utils
from stoscbots.util.loggers import LOGLEVEL

logger = logging.getLogger("Handler.Main")
logger.setLevel(LOGLEVEL)


async def _send_home(client: Client, chat_id: int) -> None:
    keyboard = keyboards.get_main_keyboard(chat_id)
    try:
        await client.send_rich_message(chat_id, keyboards.get_rich_main_menu(keyboard))
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich home menu; sending the inline keyboard")
        await client.send_message(chat_id, "What would you like to do?", reply_markup=keyboard)


# ==================================================
# Command Handlers
@Client.on_message(filters.command(["start", "hi", "hello"]) & filters.private)
@loggers.async_log_access
async def start_handler(client: Client, message: Message):
    email = None
    member_code = None
    # Check if user is authorized
    if not bot_auth.is_member(message.from_user.id):
        unauth_msg = f"Unauthorized Access by **[{message.from_user.id}:{message.from_user.username}:{message.from_user.first_name}]**\nCmd `/start`"
        await client.send_message(
            chat_id=bot_auth.get_super_admin_id(), text=unauth_msg
        )
        # Start a conversation with the user to ask for Member Code and Email
        await client.send_sticker(
            chat_id=message.from_user.id,
            sticker="CAACAgIAAxkBAAIFJV-X6UKaAAEDx4Nqup6acSBW6DlThgACoAMAAvoLtgj5yjtMiAXK4hsE",
        )
        await message.reply_text(
            "**You are not authorized to use this bot**\nHowever, if you are a STOSC member, do provide your details for access.\n\n`Enter your member code:`",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        try:
            member_code = await client.listen.Message(
                filters.text, id=filters.user(message.from_user.id), timeout=30
            )
            logger.info(f"Unauthorized Member Request Code: {member_code.text}")
            if not utils.is_valid_member_code(member_code.text):
                await message.reply_text(
                    "👎🏼 Invalid member code. Please try again: /start"
                )
                # Cancel the conversation
                await client.listen.Cancel(filters.user(message.from_user.id))
                return
        except asyncio.TimeoutError:
            await message.reply("Timed out, do type /start again")
            return
        if member_code and member_code.text == "/start":
            # Cancel the conversation
            await client.listen.Cancel(filters.user(message.from_user.id))
            return
        await message.reply_text(
            "`Enter your email or mobile number as present in church records.\nThis is only used for verification purposes:`"
        )
        try:
            email = await client.listen.Message(
                filters.text, id=filters.user(message.from_user.id), timeout=30
            )
            logger.info(f"Unauthorized Member Request Email: {email.text}")
            #  Check if email is valid
            if not utils.is_valid_email(email.text):
                await message.reply_text("👎🏼 Invalid email. Please try again: /start")
                # Cancel the conversation
                await client.listen.Cancel(filters.user(message.from_user.id))
                return
        except asyncio.TimeoutError:
            await message.reply("Timed out, do type /start again")
            return
        if email and email.text == "/start":
            # Cancel the conversation
            await client.listen.Cancel(filters.user(message.from_user.id))
            return
        if member_code and email:
            await message.reply_text(
                f"I'll inform the Managing Committee of your request. Once your ID is verified, they shall add you for access to the Bot.\n\n**Details submitted:**\n`Member Code: {member_code.text}\nEmail: {email.text}`"
            )
            # Send Telegram message to Managing Committee
            await client.send_message(
                chat_id=bot_auth.get_super_admin_id(),
                text=f"**New member request:**\nMember Code: `{member_code.text}`\nEmail: `{email.text}`\nTelegram ID: `{message.from_user.id}`",
            )
        else:
            await message.reply_text("Sorry try again")
    else:
        await _send_home(client, message.from_user.id)


# -------------------------------------------------
@Client.on_message(filters.command(["privacy"]))
@loggers.async_log_access
async def privacy_handler(client: Client, message: Message):
    try:
        async with aiofiles.open(
            "privacy_policy.txt", mode="r", encoding="utf-8"
        ) as file:
            privacy_policy = await file.read()
        await message.reply_text(
            privacy_policy,
            reply_markup=keyboards.back_to_main_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    except IOError as e:
        logging.error(f"Failed to read privacy policy file: {e}")
        await message.reply_text(
            "Sorry, the privacy policy is currently unavailable.",
            reply_markup=keyboards.back_to_main_keyboard,
        )


# -------------------------------------------------
@Client.on_message(filters.command(["help"]))
@loggers.async_log_access
@bot_auth.async_member_only
async def help_handler(client: Client, message: Message):
    """
    Handle the help command by sending a list of available commands to the user.

    :param client: The client instance.
    :param message: The incoming message object.
    """

    # Construct the help message using a list
    help_msg = [
        "**Help**",
        "➖➖",
        "Watch this [YouTube video](https://www.youtube.com/watch?v=lp8pLmTkRR4) to see how the STOSC Bot works \U0001f916",
        "\nYou can control me by sending these commands or clicking the buttons at /start:",
        "\n• /help - Show this help message",
        "• /start - Start the bot",
        "• /u [member code or name] - Search for a member by member code or Name e.g. `/u A001`",
        "• /year [year in YYYY] - Show members born on this year e.g. `/year 1976`",
        "\n** \U0001f6ab The below commands are for the management committee only: \U0001f6ab**",
        "\n• /x [member code] - Show member contributions",
        "• /xs [member code] - Show member subscriptions",
        "• /version or /ver - Show bot version",
        "• /bday  - Show this week's bday list without age",
        "• /anniv  - Show this week's anniversary list without years",
    ]

    # Join the list to form the final message
    msg = "\n".join(help_msg)

    await message.reply_text(
        msg,
        reply_markup=keyboards.back_to_main_keyboard,
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


# -------------------------------------------------
@Client.on_message(filters.command(["year"]))
@loggers.async_log_access
async def members_born_after_year_handler(client: Client, message: Message):
    if len(message.command) == 1:
        msg = "Please enter the year you want to view\ne.g. '/year 2020'"
        await message.reply_text(msg, reply_markup=keyboards.back_to_main_keyboard)
        return
    year = message.command[1]
    if utils.is_valid_year(year):
        result = db.get_members_born(year)
        if result:
            msg_parts = [
                f"**Members Born on {year}** ({len(result)})\n➖➖➖➖➖➖➖➖"
            ]
            for member in result:
                member_parts = [
                    f"\n**{member[0]}**\n",
                    f"({member[1]})\n",
                    f"{member[2]}\n",
                ]
                member_parts += [f"{member[i]}\n" for i in range(3, 6) if member[i]]
                msg_parts.append("".join(member_parts))
            await message.reply_text(
                "".join(msg_parts), reply_markup=keyboards.back_to_main_keyboard
            )
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
        if not result:
            await message.reply_text("No such Member", quote=True)
            return
        await family_profile.send_family_profile(client, message.from_user.id, result[0])
    else:
        # A search string and not member code
        result = db.get_member_details(message.command[1], "free_text")
        if not result or len(result) == 0:
            await message.reply_text("No such Member", quote=True)
        elif len(result) >= 1:
            query_str = message.command[1]
            chat_id = message.from_user.id
            listing_kb = keyboards.get_member_listing_keyboard(result)
            fallback = (
                f"🔎 Search results for `{query_str}`\n"
                "➖➖➖➖➖➖➖➖➖➖➖\n"
                "`🏠 = Head of Household`\n"
                "`🌱 = Child`"
            )
            try:
                rich_card = keyboards.get_rich_member_search_results(query_str, result)
                await client.send_rich_message(
                    chat_id,
                    rich_card,
                    reply_markup=keyboards.back_to_main_keyboard,
                )
            except RichMessageUnsupported:
                logger.warning("Telegram rejected rich member search results; sending plain text")
                await message.reply_text(
                    fallback,
                    reply_markup=listing_kb,
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )


# -------------------------------------------------
# Command Handlers
@Client.on_message(filters.command(["t"]))
@loggers.async_log_access
@bot_auth.async_member_only
async def mobile_search_cmd_handler(client: Client, message: Message):
    if len(message.command) != 2:
        msg = "Please enter a Singapore Telephone to search\n e.g. `/u 99999999`"
        await message.reply_text(msg, quote=True)
        return

    # Normalize the telephone number i.e. remove spaces and hyphens and international codes if any
    mobile_number = utils.normalize_telephone(message.command[1])
    if not utils.valid_telephone(mobile_number):
        await message.reply_text("Invalid Singapore Number", quote=True)
        return

    # Search for a member by telephone number
    result = db.get_member_details(mobile_number, "mobile")

    if not result or len(result) == 0:
        await message.reply_text("No STOSC member has that number", quote=True)
    else:
        for row in result:
            await family_profile.send_family_profile(client, message.from_user.id, row)


# ==================================================
"""
Handle multiple callback queries data and return filter for each
"""


def dynamic_data_filter1(data):
    return filters.create(
        lambda flt, _, query: flt.data == query.data,
        data=data,  # "data" kwarg is accessed with "flt.data" above
    )


def dynamic_data_filter2(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data),
        data=data,
        # "data" kwarg is accessed with "flt.data" above
    )


# ==================================================
# Callback Handlers (for Buttons)
@Client.on_callback_query(filters.regex(rf"\A{family_profile.RELATED_FAMILY_PREFIX}([A-Z][0-9]{{3}})\Z"))
@loggers.async_log_access
@bot_auth.async_member_only
async def related_family_handler(client: Client, query: CallbackQuery):
    if not query.matches:
        await query.answer("Invalid family link", show_alert=True)
        return
    code = query.matches[0].group(1)
    result = db.get_member_details(code, "code")
    if not result:
        await query.answer(f"No such family: {code}", show_alert=True)
        return
    await query.answer()
    await family_profile.send_family_profile(client, query.from_user.id, result[0])


@Client.on_callback_query(dynamic_data_filter1("Main Menu"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_main_menu(client: Client, query: CallbackQuery):
    await query.answer()
    await _send_home(client, query.from_user.id)


# -------------------------------------------------
# Callback Handlers (for Buttons)
@Client.on_callback_query(dynamic_data_filter1("Services Menu"))
@loggers.async_log_access
async def show_services_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    fallback = (
        "➖➖**Services Menu**➖➖\n\n"
        "• Sunday Holy Qurbana: 8:00 AM (Matins), 9:00 AM (Qurbana)\n"
        "• Saturday Evening Prayer: 6:30 PM\n"
        "• Wednesday Intercession: 7:30 PM\n\n"
        "📜 [Liturgical Calendar](https://stosc.com/calendar/)\n"
        "🙏 [Submit Prayer Request](https://stosc.com/pr)\n"
        "▶️ [Cathedral Livestream](https://stosc.com/live/)"
    )
    try:
        rich_card = keyboards.get_rich_services_menu()
        await client.send_rich_message(
            chat_id,
            rich_card,
            reply_markup=keyboards.services_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected rich services menu; sending plain text")
        await client.send_message(
            chat_id,
            fallback,
            reply_markup=keyboards.services_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Members Menu"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_members_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    try:
        await client.send_rich_message(chat_id, keyboards.get_rich_members_menu())
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich members menu; sending the inline keyboard")
        await client.send_message(chat_id, "Members", reply_markup=keyboards.members_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Prayer Groups Menu"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_prayer_groups_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    try:
        await client.send_rich_message(
            chat_id,
            keyboards.get_rich_prayer_groups_menu(),
            reply_markup=keyboards.area_prayer_groups_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich prayer groups menu; sending the inline keyboard")
        await client.send_message(chat_id, "Area Prayer Groups", reply_markup=keyboards.area_prayer_groups_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Finance Menu"))
@loggers.async_log_access
@bot_auth.async_management_only
async def show_finance_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    fallback_text = (
        "➖➖**Finance Menu**➖➖\n\n"
        "Member Ledger Commands:\n"
        "• `/x <CODE>` — Member contributions & payments\n"
        "• `/xs <CODE>` — Member invoices & dues"
    )
    try:
        await client.send_rich_message(
            chat_id,
            keyboards.get_rich_finance_menu(),
            reply_markup=keyboards.finance_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich finance menu; sending plain text")
        await client.send_message(
            chat_id,
            fallback_text,
            reply_markup=keyboards.finance_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("My Details Menu"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_my_details_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    try:
        await client.send_rich_message(chat_id, keyboards.get_rich_my_details_menu())
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich my details menu; sending the inline keyboard")
        await client.send_message(chat_id, "My Details", reply_markup=keyboards.my_details_menu_keyboard)


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("My Harvest Festival Menu"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_my_harvest_festival_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    member_code = utils.getMemberCode_from_TelegramID(chat_id)

    purchases_data = utils.get_member_auction_purchases_data(member_code)
    contributions_data = utils.get_member_auction_contributions_data(member_code)
    portal_link = utils.get_member_auction_link(member_code) or None

    fallback_lines = ["**🌽 My Harvest Details Menu** 🌽\n`Your activity from the Harvest Festival`"]
    purchases_text = utils.generate_msg_member_auction_purchases(member_code)
    if purchases_text:
        fallback_lines.append(purchases_text)
    contributions_text = utils.generate_msg_member_auction_contributions(member_code)
    if contributions_text:
        fallback_lines.append(contributions_text)
    if portal_link:
        fallback_lines.append(f"▪️ Auction Link: {portal_link}")
    fallback_text = "\n\n".join(fallback_lines)

    try:
        rich_menu = keyboards.get_rich_harvest_festival_menu(
            member_code=member_code,
            purchases_data=purchases_data,
            contributions_data=contributions_data,
            auction_portal_url=portal_link,
        )
        await client.send_rich_message(
            chat_id,
            rich_menu,
            reply_markup=keyboards.harvest_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich Harvest Festival card; sending plain text")
        await client.send_message(
            chat_id,
            fallback_text,
            reply_markup=keyboards.harvest_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("PayNow Menu"))
@loggers.async_log_access
@bot_auth.async_member_only
async def show_paynow_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    fallback_text = (
        "**Payment Options**\n➖➖➖➖➖➖\n"
        "You may pay by one of these ways:\n"
        "• PayNow to UEN: `S79SS0001L`\n"
        "• Bank transfer to DBS: `0480155596`\n"
        "• Cash or Cheque (payable to `St. Thomas Orthodox Syrian Cathedral`) at the church office\n\n"
        "`Please mention your family code and purpose of contribution.`\n"
        "For multiple payments, email the breakdown to accounts@stosc.com"
    )

    async def send_rich(include_photo: bool) -> None:
        await client.send_rich_message(
            chat_id,
            keyboards.get_rich_paynow_menu(include_photo=include_photo),
            reply_markup=keyboards.paynow_keyboard,
        )

    try:
        try:
            await send_rich(include_photo=True)
        except family_profile.PHOTO_ERRORS as exc:
            logger.warning("Telegram could not process PayNow photo (%s); retrying without it", type(exc).__name__)
            await send_rich(include_photo=False)
    except RichMessageUnsupported:
        logger.warning("Telegram rejected the rich PayNow card; sending plain text")
        await client.send_message(
            chat_id,
            fallback_text,
            reply_markup=keyboards.paynow_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
@Client.on_callback_query(dynamic_data_filter1("Streaming Menu"))
@loggers.async_log_access
@bot_auth.async_management_only
async def show_streaming_menu(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id
    fallback = (
        "➖➖**Streaming Menu**➖➖\n\n"
        "• Weekly Announcement Slides: Tap button below to generate\n"
        "• [Google Drive Slides](https://drive.google.com/drive/folders/13YnRvL9JZoGbeMXQ1T9E7vhaEZEFfUK8)\n"
        "• [Cathedral Livestream](https://stosc.com/live/)"
    )
    try:
        rich_card = keyboards.get_rich_streaming_menu()
        await client.send_rich_message(
            chat_id,
            rich_card,
            reply_markup=keyboards.streaming_menu_keyboard,
        )
    except RichMessageUnsupported:
        logger.warning("Telegram rejected rich streaming menu; sending plain text")
        await client.send_message(
            chat_id,
            fallback,
            reply_markup=keyboards.streaming_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


# --------------------------------------------------
# Handler for buttons generated from /u MyName search command
@Client.on_callback_query(dynamic_data_filter2("Member_"))
@loggers.async_log_access
@bot_auth.async_member_only
async def member_search_button_handler(client: Client, query: CallbackQuery):
    await query.answer()
    person_ID = query.data.split("_")[2]
    result = db.get_member_details(person_ID, "person")
    if not result:
        await client.send_message(query.from_user.id, "No member details found.")
        return
    await family_profile.send_person_profile(
        client,
        query.from_user.id,
        result[0],
        person_ID,
    )
