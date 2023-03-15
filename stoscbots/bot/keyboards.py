from faker import Faker
import random
import string
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from stoscbots.util import bot_auth
from datetime import datetime, date

web_app_pr: WebAppInfo = WebAppInfo(url="https://docs.google.com/forms/d/e/1FAIpQLSdJ0SQTC487_RwjdnbBVq5sHyfsXhC2PZyDmL63K4GJvp-BVA/viewform")

fake = Faker()
def generate_random_memberID():
    # Choose a random character
    char = random.choice(string.ascii_uppercase)
    # Choose 3 random digits
    digits = "".join(random.choices(string.digits, k=3))
    # Concatenate the character and digits
    return char + digits

# --------------------------------------------------------------------------------------------------
"""
InlineKeyboardButton = Buttons that belong to a Keyboard
"""
__BACK_TO_MAIN_BUTTON = InlineKeyboardButton("🔙 Return to Main menu", callback_data = "Main Menu")
__MAIN_SERVICES_BUTTON = InlineKeyboardButton("✝ Services", callback_data = "Services Menu")
__MAIN_MEMBERS_BUTTON = InlineKeyboardButton("👨‍👩‍👦 Members", callback_data = "Members Menu")
__MAIN_PRAYER_GROUPS_BUTTON = InlineKeyboardButton("🤲🏻 Prayer Groups", callback_data = "Prayer Groups Menu")
__MAIN_FINANCE_BUTTON = InlineKeyboardButton("💲 Finance", callback_data = "Finance Menu")
__MAIN_ST_MARYS_BUTTON = InlineKeyboardButton("👩🏻 St. Marys", callback_data = "St. Marys Menu")
__MAIN_MY_DETAILS_BUTTON = InlineKeyboardButton("👨🏻 My Details 👩🏻", callback_data = "My Details Menu")
__MAIN_MY_HARVEST_BUTTON = InlineKeyboardButton("🌽 My Harvest Festival", callback_data = "My Harvest Festival Menu")
__MAIN_PAYNOW_BUTTON = InlineKeyboardButton("💵 PayNow", callback_data = "PayNow Menu")

__MEMBERS_BDAY_TODAY_BUTTON = InlineKeyboardButton("🎂 Birthdays today", callback_data = "Member Birthday Today Button")
__MEMBERS_BDAY_WEEK_BUTTON = InlineKeyboardButton("🎂 Birthdays this week", callback_data = "Member Birthday Week Button")
__MEMBERS_ANNIVERSARY_TODAY_BUTTON = InlineKeyboardButton("💍 Anniversaries today", callback_data = "Member Anniversary Today Button")
__MEMBERS_ANNIVERSARY_WEEK_BUTTON = InlineKeyboardButton("💍 Anniversaries this week", callback_data = "Member Anniversary Week Button")
__MEMBERS_GB_INELIGIBLE_BUTTON = InlineKeyboardButton("💼 GB", callback_data = "GB")

__FINANCE_EXEC_SUMMARY_BUTTON = InlineKeyboardButton("Executive Summary", callback_data = "Finance Executive Summary Button")
__FINANCE_BANK_SUMMARY_BUTTON = InlineKeyboardButton("Bank Summary", callback_data = "Finance Bank Summary Button")
__FINANCE_TRIAL_INC_BAL_BUTTON = InlineKeyboardButton("Trial Bal Revenue", callback_data = "Finance Trial Balance Revenue Button")
__FINANCE_TRIAL_EXP_BAL_BUTTON = InlineKeyboardButton("Trial Bal Expense", callback_data = "Finance Trial Balance Expense Button")
__FINANCE_PAYMENTS_WTD_BUTTON = InlineKeyboardButton("Payments WTD", callback_data = "Finance Payments WTD Button")
__FINANCE_LATEST_TX_BUTTON = InlineKeyboardButton("Latest Transactions", callback_data = "Finance Latest Transactions Button")
__FINANCE_OUTSTANDINGS_BUTTON = InlineKeyboardButton("Outstanding", callback_data = "Finance Outstanding Button")
__FINANCE_TRACK_BUTTON = InlineKeyboardButton("Projects", callback_data = "Finance Projects Button")

__ST_MARYS_EXEC_SUMMARY_BUTTON = InlineKeyboardButton("📊 Projects Summary", callback_data = "St. Marys Project Summary Button")

__MYDETAILS_MY_PROFILE_BUTTON = InlineKeyboardButton("🧾 My Profile", callback_data = "My Profile")
__MYDETAILS_MY_CONTRIBUTIONS_BUTTON = InlineKeyboardButton("💳 My Contributions", callback_data = "My Contributions")
__MYDETAILS_MY_SUBSCRIPTIONS_BUTTON = InlineKeyboardButton("📜 My Dues", callback_data = "My Dues")
__MYDETAILS_PRAYER_REQUESTS_BUTTON = InlineKeyboardButton("🙏🏽 Submit Prayer Requests", web_app=web_app_pr)
__MYDETAILS_LIST_OF_ACCOUNTS_BUTTON = InlineKeyboardButton("ℹ List of Accounts", callback_data = "List of Accounts")

__PRAYER_REQUESTS_LISTING_BUTTON = InlineKeyboardButton("📿 Prayer Requests", callback_data = "Prayer Requests")
__WHO_IS_MY_MC_BUTTON = InlineKeyboardButton("👥 Management Committee", callback_data = "MC")
# ---------------------------------------------------------------------------------------------------
'''
Assemble the Buttons above to create Keyboards
'''
back_to_main_keyboard = InlineKeyboardMarkup([
    [__BACK_TO_MAIN_BUTTON]
])

members_menu_keyboard = InlineKeyboardMarkup([
    [__MEMBERS_BDAY_TODAY_BUTTON, __MEMBERS_ANNIVERSARY_TODAY_BUTTON],
    [__MEMBERS_BDAY_WEEK_BUTTON, __MEMBERS_ANNIVERSARY_WEEK_BUTTON],
    [__WHO_IS_MY_MC_BUTTON, __MEMBERS_GB_INELIGIBLE_BUTTON],
    [__BACK_TO_MAIN_BUTTON, ]
])

finance_menu_keyboard = InlineKeyboardMarkup([
    [__FINANCE_EXEC_SUMMARY_BUTTON, __FINANCE_BANK_SUMMARY_BUTTON],
    [__FINANCE_TRIAL_INC_BAL_BUTTON, __FINANCE_TRIAL_EXP_BAL_BUTTON],
    [__FINANCE_LATEST_TX_BUTTON, __FINANCE_PAYMENTS_WTD_BUTTON],
    [__FINANCE_OUTSTANDINGS_BUTTON, __FINANCE_TRACK_BUTTON],
    [__BACK_TO_MAIN_BUTTON]
])

stmarys_menu_keyboard = InlineKeyboardMarkup([
    [__ST_MARYS_EXEC_SUMMARY_BUTTON],
    [__BACK_TO_MAIN_BUTTON]
])

area_prayer_groups_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("East Coast", callback_data = "Area Prayer Group 1"),
            InlineKeyboardButton("Houg|Seng|Pung", callback_data = "Area Prayer Group 2")
        ],
        [
            InlineKeyboardButton("Choa Chu Kang", callback_data = "Area Prayer Group 3"),
            InlineKeyboardButton("Jurong", callback_data = "Area Prayer Group 4")
        ],
        [
            InlineKeyboardButton("Woodlands", callback_data = "Area Prayer Group 5"),
            InlineKeyboardButton("Central", callback_data = "Area Prayer Group 6")
        ],
        [
            InlineKeyboardButton("Church Area", callback_data = "Area Prayer Group 7"),
            __BACK_TO_MAIN_BUTTON
        ]
    ])

my_details_menu_keyboard = InlineKeyboardMarkup([
    [__MYDETAILS_MY_PROFILE_BUTTON],
    [__MYDETAILS_MY_CONTRIBUTIONS_BUTTON, __MYDETAILS_LIST_OF_ACCOUNTS_BUTTON],
    [__MYDETAILS_MY_SUBSCRIPTIONS_BUTTON, __MYDETAILS_PRAYER_REQUESTS_BUTTON],
    [__BACK_TO_MAIN_BUTTON]
])

harvest_menu_keyboard = InlineKeyboardMarkup([
    [__BACK_TO_MAIN_BUTTON, InlineKeyboardButton("🔃 Refresh", callback_data = "My Harvest Festival Menu")]
])
# ---------------------------------------------------------------------------------------------------
"""
Dynamic keyboards that have to be created at runtime:
"""

def get_main_keyboard(telegram_id):
    if bot_auth.is_mgmt_member(telegram_id):
        keyboard_main = InlineKeyboardMarkup([
            [__MAIN_SERVICES_BUTTON],
            [__MAIN_MEMBERS_BUTTON,__MAIN_PRAYER_GROUPS_BUTTON],
            [__MAIN_FINANCE_BUTTON,__MAIN_ST_MARYS_BUTTON],
            [__MAIN_MY_DETAILS_BUTTON,__MAIN_MY_HARVEST_BUTTON],
            [__MAIN_PAYNOW_BUTTON]
            ])
    elif bot_auth.is_st_marys_member(telegram_id):
        keyboard_main = InlineKeyboardMarkup([
            [__MAIN_MEMBERS_BUTTON,__MAIN_PRAYER_GROUPS_BUTTON],
            [__MAIN_ST_MARYS_BUTTON],
            [__MAIN_MY_DETAILS_BUTTON,__MAIN_MY_HARVEST_BUTTON],
            [__MAIN_PAYNOW_BUTTON]
            ])
    else:
        # Normal members
        keyboard_main = InlineKeyboardMarkup([
            [__MAIN_MEMBERS_BUTTON, __MAIN_PRAYER_GROUPS_BUTTON],
            [__MAIN_MY_DETAILS_BUTTON,__MAIN_MY_HARVEST_BUTTON],
            [__MAIN_PAYNOW_BUTTON]
            ])
    return keyboard_main


# Dynamically generate a keyboard with prayer requests
def get_services_keyboard():
    # Kerboard is a double List
    keyboard = []
    keyboard.append([__BACK_TO_MAIN_BUTTON, __PRAYER_REQUESTS_LISTING_BUTTON])
    return InlineKeyboardMarkup(keyboard)

# Generate a Keyboard of member search results
def get_member_listing_keyboard(results):
    # Kerboard is a double List
    keyboard = []
    _keyboard_rows = []

    cols_per_row = 2

    for _counter, _item in enumerate(results):
        icon = ''

        # Head of Family
        if _item[23] == 1:
            icon += '⚡'
        # If Age and Gender data both are available
        # Person's DOB in '1964-04-10'
        if _item[20]:
            age = date.today().year - int(_item[20].split('-')[0])
        else:
            age = None
        if age:
            if age <= 18:
                if _item[22] == 1:
                    icon += '👦🏻'
                elif _item[22] == 2:
                    icon += '👧🏻'
            elif age > 18:
                # Gender
                if _item[22] == 1:
                    icon += '🧔🏻'
                elif _item[22] == 2:
                    icon += '👩🏻'
        else:
            # No age data, check only Gender:
            if _item[22] == 1:
                icon += '♂'
            elif _item[22] == 2:
                icon += '♀'
        _keyboard_text=f"{icon} {fake.name()} ({_item[1]}) »"
        _keyboard_rows.append(
            InlineKeyboardButton(
                _keyboard_text, callback_data = f"Member_{_item[1]}_{_item[25]}"
            )
        )
        # For every 2 cols in a row
        if (_counter + 1) % cols_per_row == 0:
            # Add the rows to the main keyboard
            keyboard.append(_keyboard_rows)
            # Reinitialize the row
            _keyboard_rows = []
    _keyboard_rows.append(__BACK_TO_MAIN_BUTTON)
    keyboard.append(_keyboard_rows)
    return InlineKeyboardMarkup(keyboard)