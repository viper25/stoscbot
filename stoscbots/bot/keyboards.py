from datetime import date

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from stoscbots.util import bot_auth

WEB_APP_PR = WebAppInfo(
    url="https://forms.office.com/r/ThXjcLLr5Z")


# Define a function to create a button to avoid repetitive code
def create_button(text, callback_data, web_app=None):
    return InlineKeyboardButton(text, callback_data=callback_data, web_app=web_app)


# --------------------------------------------------------------------------------------------------
"""
InlineKeyboardButton = Buttons that belong to a Keyboard
"""
BACK_TO_MAIN_BUTTON = InlineKeyboardButton("🔙 Return to Main menu", callback_data="Main Menu")
__MAIN_SERVICES_BUTTON = InlineKeyboardButton("✝ Services", callback_data="Services Menu")
__MAIN_MEMBERS_BUTTON = InlineKeyboardButton("👨‍👩‍👦 Members", callback_data="Members Menu")
__MAIN_PRAYER_GROUPS_BUTTON = InlineKeyboardButton("🤲🏻 Prayer Groups", callback_data="Prayer Groups Menu")
__MAIN_FINANCE_BUTTON = InlineKeyboardButton("💲 Finance", callback_data="Finance Menu")
__MAIN_MY_DETAILS_BUTTON = InlineKeyboardButton("👨🏻 My Details 👩🏻", callback_data="My Details Menu")
__MAIN_MY_HARVEST_BUTTON = InlineKeyboardButton("🌽 My Harvest Festival", callback_data="My Harvest Festival Menu")
__MAIN_PAYNOW_BUTTON = InlineKeyboardButton("💵 PayNow", callback_data="PayNow Menu")

__MEMBERS_BDAY_TODAY_BUTTON = InlineKeyboardButton("🎂 Birthdays today", callback_data="Member Birthday Today Button")
__MEMBERS_NEW_BUTTON = InlineKeyboardButton("🆕 New members", callback_data="New Members Button")
__MEMBERS_BDAY_WEEK_BUTTON = InlineKeyboardButton("🎂 Birthdays this week", callback_data="Member Birthday Week Button")
__MEMBERS_ANNIVERSARY_TODAY_BUTTON = InlineKeyboardButton("💍 Anniversaries today",
                                                          callback_data="Member Anniversary Today Button")
__MEMBERS_ANNIVERSARY_WEEK_BUTTON = InlineKeyboardButton("💍 Anniversaries this week",
                                                         callback_data="Member Anniversary Week Button")
__MEMBERS_GB_INELIGIBLE_BUTTON = InlineKeyboardButton("💼 GB", callback_data="GB")

__FINANCE_EXEC_SUMMARY_BUTTON = InlineKeyboardButton("Executive Summary",
                                                     callback_data="Finance Executive Summary Button")
__FINANCE_BANK_SUMMARY_BUTTON = InlineKeyboardButton("Bank Summary", callback_data="Finance Bank Summary Button")
__FINANCE_TRIAL_INC_BAL_BUTTON = InlineKeyboardButton("Trial Bal Revenue",
                                                      callback_data="Finance Trial Balance Revenue Button")
__FINANCE_TRIAL_EXP_BAL_BUTTON = InlineKeyboardButton("Trial Bal Expense",
                                                      callback_data="Finance Trial Balance Expense Button")
__FINANCE_PAYMENTS_WTD_BUTTON = InlineKeyboardButton("Payments WTD", callback_data="Finance Payments WTD Button")
__FINANCE_LATEST_TX_BUTTON = InlineKeyboardButton("Latest Transactions",
                                                  callback_data="Finance Latest Transactions Button")
__FINANCE_OUTSTANDINGS_BUTTON = InlineKeyboardButton("Outstanding", callback_data="Finance Outstanding Button")
__FINANCE_TRACK_BUTTON = InlineKeyboardButton("Projects", callback_data="Finance Projects Button")

__MYDETAILS_MY_PROFILE_BUTTON = InlineKeyboardButton("🧾 My Profile", callback_data="My Profile")
__MYDETAILS_MY_CONTRIBUTIONS_BUTTON = InlineKeyboardButton("💳 My Contributions", callback_data="My Contributions")
__MYDETAILS_MY_SUBSCRIPTIONS_BUTTON = InlineKeyboardButton("📜 My Dues", callback_data="My Dues")
__MYDETAILS_PRAYER_REQUESTS_BUTTON = InlineKeyboardButton("🙏🏽 Submit Prayer Requests", web_app=WEB_APP_PR)
__MYDETAILS_LIST_OF_ACCOUNTS_BUTTON = InlineKeyboardButton("ℹ List of Accounts", callback_data="List of Accounts")

__WHO_IS_MY_MC_BUTTON = InlineKeyboardButton("👥 Management Committee", callback_data="MC")
__MAIN_STREAMING_BUTTON = InlineKeyboardButton("📡 Streaming", callback_data="Streaming Menu")
__STREAMING_GEN_ANNOUNCEMENT_SLIDES_BUTTON = InlineKeyboardButton("📺 Generate Announcement Slides",
                                                                  callback_data="Generate Announcement Slides")

__MAIN_ADMIN_BUTTON = InlineKeyboardButton("🔐 Admin", callback_data="Admin Menu")
__SHOW_STATS_BUTTON = InlineKeyboardButton("📊 Show Stats", callback_data="Show Stats")
__LOGS_BUTTON = InlineKeyboardButton("📜 Display Logs", callback_data="Show Logs")
__ERROR_LOGS_BUTTON = InlineKeyboardButton("📜🚩 Display Error Logs", callback_data="Show Error Logs")
# ---------------------------------------------------------------------------------------------------
'''
Assemble the Buttons above to create Keyboards
'''
back_to_main_keyboard = InlineKeyboardMarkup([
    [BACK_TO_MAIN_BUTTON]
])

members_menu_keyboard = InlineKeyboardMarkup([
    [__MEMBERS_BDAY_TODAY_BUTTON, __MEMBERS_ANNIVERSARY_TODAY_BUTTON],
    [__MEMBERS_BDAY_WEEK_BUTTON, __MEMBERS_ANNIVERSARY_WEEK_BUTTON],
    [__WHO_IS_MY_MC_BUTTON, __MEMBERS_GB_INELIGIBLE_BUTTON],
    [__MEMBERS_NEW_BUTTON],
    [BACK_TO_MAIN_BUTTON, ]
])

finance_menu_keyboard = InlineKeyboardMarkup([
    [__FINANCE_EXEC_SUMMARY_BUTTON, __FINANCE_BANK_SUMMARY_BUTTON],
    [__FINANCE_TRIAL_INC_BAL_BUTTON, __FINANCE_TRIAL_EXP_BAL_BUTTON],
    [__FINANCE_LATEST_TX_BUTTON, __FINANCE_PAYMENTS_WTD_BUTTON],
    [__FINANCE_OUTSTANDINGS_BUTTON, __FINANCE_TRACK_BUTTON],
    [BACK_TO_MAIN_BUTTON]
])

area_prayer_groups_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("East Coast", callback_data="Area Prayer Group 1"),
        InlineKeyboardButton("Houg|Seng|Pung", callback_data="Area Prayer Group 2")
    ],
    [
        InlineKeyboardButton("Choa Chu Kang", callback_data="Area Prayer Group 3"),
        InlineKeyboardButton("Jurong", callback_data="Area Prayer Group 4")
    ],
    [
        InlineKeyboardButton("Woodlands", callback_data="Area Prayer Group 5"),
        InlineKeyboardButton("Central", callback_data="Area Prayer Group 6")
    ],
    [
        InlineKeyboardButton("Church Area", callback_data="Area Prayer Group 7"),
        BACK_TO_MAIN_BUTTON
    ]
])

my_details_menu_keyboard = InlineKeyboardMarkup([
    [__MYDETAILS_MY_PROFILE_BUTTON],
    [__MYDETAILS_MY_CONTRIBUTIONS_BUTTON, __MYDETAILS_LIST_OF_ACCOUNTS_BUTTON],
    [__MYDETAILS_MY_SUBSCRIPTIONS_BUTTON, __MYDETAILS_PRAYER_REQUESTS_BUTTON],
    [BACK_TO_MAIN_BUTTON]
])

harvest_menu_keyboard = InlineKeyboardMarkup([
    [BACK_TO_MAIN_BUTTON, InlineKeyboardButton("🔃 Refresh", callback_data="My Harvest Festival Menu")]
])

streaming_menu_keyboard = InlineKeyboardMarkup([
    [__STREAMING_GEN_ANNOUNCEMENT_SLIDES_BUTTON],
    [BACK_TO_MAIN_BUTTON]
])

admin_menu_keyboard = InlineKeyboardMarkup([
    [__SHOW_STATS_BUTTON, __LOGS_BUTTON],
    [__ERROR_LOGS_BUTTON, BACK_TO_MAIN_BUTTON]
])
# ---------------------------------------------------------------------------------------------------
"""
Dynamic keyboards that have to be created at runtime:
"""


def get_main_keyboard(telegram_id):
    if bot_auth.is_super_admin(telegram_id) or bot_auth.is_mgmt_member(telegram_id):
        buttons = [
            [__MAIN_SERVICES_BUTTON, __MAIN_MEMBERS_BUTTON],
            [__MAIN_PRAYER_GROUPS_BUTTON, __MAIN_FINANCE_BUTTON],
            [__MAIN_MY_DETAILS_BUTTON, __MAIN_MY_HARVEST_BUTTON],
            [__MAIN_PAYNOW_BUTTON, __MAIN_STREAMING_BUTTON]
        ]
        if bot_auth.is_super_admin(telegram_id):
            buttons.append([__MAIN_ADMIN_BUTTON])
    else:
        # Normal members
        buttons = [
            [__MAIN_MEMBERS_BUTTON, __MAIN_PRAYER_GROUPS_BUTTON],
            [__MAIN_MY_DETAILS_BUTTON, __MAIN_MY_HARVEST_BUTTON],
            [__MAIN_PAYNOW_BUTTON]
        ]
    return InlineKeyboardMarkup(buttons)


# Dynamically generate a keyboard with prayer requests
def get_services_keyboard():
    return InlineKeyboardMarkup([[BACK_TO_MAIN_BUTTON]])


def get_icon(item):
    icon = '⚡' if item[23] == 1 else ''

    age = None
    if item[20]:
        age = date.today().year - int(item[20].split('-')[0])

    gender_icon_map = {
        (1, 'child'): '👦🏻',
        (2, 'child'): '👧🏻',
        (1, 'adult'): '🧔🏻',
        (2, 'adult'): '👩🏻',
        (1, None): '♂',
        (2, None): '♀'
    }

    age_group = 'child' if age and age <= 18 else 'adult' if age and age > 18 else None
    icon += gender_icon_map.get((item[22], age_group), '')

    return icon


def get_member_listing_keyboard(results):
    keyboard = []
    keyboard_rows = []
    cols_per_row = 2

    for counter, item in enumerate(results):
        icon = get_icon(item)
        keyboard_text = f"{icon} {item[24]} ({item[1]}) »"
        keyboard_rows.append(InlineKeyboardButton(keyboard_text, callback_data=f"Member_{item[1]}_{item[25]}"))

        if (counter + 1) % cols_per_row == 0:
            keyboard.append(keyboard_rows)
            keyboard_rows = []

    keyboard_rows.append(BACK_TO_MAIN_BUTTON)
    keyboard.append(keyboard_rows)

    return InlineKeyboardMarkup(keyboard)
