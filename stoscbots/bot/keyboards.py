from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from stoscbots.util import bot_auth
from datetime import datetime, date
# --------------------------------------------------------------------------------------------------
"""
InlineKeyboardButton = Buttons that belong to a Keyboard
"""
__back_to_main_button = InlineKeyboardButton("🔙 Return to Main menu", callback_data="Main Menu")
__main_services_button = InlineKeyboardButton("✝ Services", callback_data="Services Menu")
__main_members_button = InlineKeyboardButton("👨‍👩‍👦 Members", callback_data="Members Menu")
__main_prayer_groups_button = InlineKeyboardButton("🤲🏻 Prayer Groups", callback_data="Prayer Groups Menu")
__main_finance_button = InlineKeyboardButton("💲 Finance", callback_data="Finance Menu")
__main_my_details_button = InlineKeyboardButton("👨🏻 My Details 👩🏻", callback_data="My Details Menu")
__main_my_harvest_button = InlineKeyboardButton("My Harvest Festival 🌽", callback_data="My Harvest Festival Menu")
__main_paynow_button = InlineKeyboardButton("💵 PayNow", callback_data="PayNow Menu")

__members_details_button = InlineKeyboardButton("Member Details", callback_data="Member Details Button")
__members_bday_today_button = InlineKeyboardButton("🎂 Birthdays today", callback_data="Member Birthday Today Button")
__members_bday_week_button = InlineKeyboardButton("🎂 Birthdays this week", callback_data="Member Birthday Week Button")
__members_anniversary_today_button = InlineKeyboardButton("💍 Anniversaries today", callback_data="Member Anniversary Today Button")
__members_anniversary_week_button = InlineKeyboardButton("💍 Anniversaries this week", callback_data="Member Anniversary Week Button")

__finance_exec_summary_button = InlineKeyboardButton("Executive Summary", callback_data="Finance Executive Summary Button")
__finance_bank_summary_button = InlineKeyboardButton("Bank Summary", callback_data="Finance Bank Summary Button")
__finance_trial_bal_button = InlineKeyboardButton("Trial Balance", callback_data="Finance Trial Balance Button")
__finance_payments_wtd_button = InlineKeyboardButton("Payments WTD", callback_data="Finance Payments WTD Button")
__finance_latest_tx_button = InlineKeyboardButton("Latest Transactions", callback_data="Finance Latest Transactions Button")
__finance_member_bal_button = InlineKeyboardButton("ℹ Help", callback_data="Finance Help Button")

__mydetails_my_profile_button = InlineKeyboardButton("🧾 My Profile", callback_data="My Profile")
__mydetails_my_contributions_button = InlineKeyboardButton("💳 My Contributions", callback_data="My Contributions")
__mydetails_my_subscriptions_button = InlineKeyboardButton("📜 My Subscriptions", callback_data="My Subscriptions")
__mydetails_help_button = InlineKeyboardButton("ℹ Help", callback_data="Help")
__mydetails_list_of_accounts_button = InlineKeyboardButton("ℹ List of Accounts", callback_data="List of Accounts")

# ---------------------------------------------------------------------------------------------------
'''
Assemble the Buttons above to create Keyboards
'''
back_to_main_keyboard = InlineKeyboardMarkup([
    [__back_to_main_button]
])

members_menu_keyboard = InlineKeyboardMarkup([
    [__members_bday_today_button,__members_anniversary_today_button],
    [__members_bday_week_button,__members_anniversary_week_button],
    [__back_to_main_button]
])

finance_menu_keyboard = InlineKeyboardMarkup([
    [__finance_exec_summary_button,__finance_bank_summary_button],
    [__finance_trial_bal_button,__finance_payments_wtd_button],
    [__finance_latest_tx_button,__finance_member_bal_button],
    [__back_to_main_button]
])

area_prayer_groups_keyboard=InlineKeyboardMarkup([
        [
            InlineKeyboardButton("East Coast", callback_data=f"Area Prayer Group 1"),
            InlineKeyboardButton("Houg|Seng|Pung", callback_data=f"Area Prayer Group 2")
        ],
        [
            InlineKeyboardButton("Choa Chu Kang", callback_data=f"Area Prayer Group 3"),
            InlineKeyboardButton("Jurong", callback_data=f"Area Prayer Group 4")
        ],
        [
            InlineKeyboardButton("Woodlands", callback_data=f"Area Prayer Group 5"),
            InlineKeyboardButton("Central", callback_data=f"Area Prayer Group 6")
        ],
        [
            InlineKeyboardButton("Church Area", callback_data=f"Area Prayer Group 7"),
            __back_to_main_button
        ]
    ])

my_details_menu_keyboard = InlineKeyboardMarkup([
    [__mydetails_my_profile_button],
    [__mydetails_my_contributions_button,__mydetails_my_subscriptions_button],
    [__mydetails_help_button,__mydetails_list_of_accounts_button],
    [__back_to_main_button]
])
# ---------------------------------------------------------------------------------------------------
"""
Dynamic keyboards that have to be created at runtime:
"""

def get_main_keyboard(telegram_id):
    if bot_auth.is_mgmt_member(telegram_id):
        keyboard_main = InlineKeyboardMarkup([
            [__main_services_button],
            [__main_members_button,__main_prayer_groups_button],
            [__main_finance_button],
            [__main_my_details_button,__main_my_harvest_button],
            [__main_paynow_button]
            ])
    else:
        # Normal members
        keyboard_main = InlineKeyboardMarkup([
            [__main_services_button,__main_prayer_groups_button],
            [__main_my_details_button,__main_my_harvest_button],
            [__main_paynow_button]
            ])
    return keyboard_main


# Dynamically generate a keyboard with upcoming services
def get_services_keyboard(next_services):
    _counter=0
    # Kerboard is a double List
    keyboard=[]
    _keyboard_rows=[]

    cols_per_row=2

    for _item in next_services:
        _counter += 1
        if datetime.now() > _item[2]:
            _keyboard_text=f'🔒 {_item[2].strftime("%b %d")} registrations »'            
        else:
            _keyboard_text=f'{_item[2].strftime("%b %d")} registrations »'
        _keyboard_rows.append(
            InlineKeyboardButton(
                _keyboard_text, callback_data="Registrations for Service " + str(_item[0])
            )
        )
        # For every 2 cols in a row
        if _counter % cols_per_row == 0:
            # Add the rows to the main keyboard
            keyboard.append(_keyboard_rows)
            # Reinitialize the row
            _keyboard_rows=[]
    _keyboard_rows.append(__main_services_button)
    keyboard.append(_keyboard_rows)
    keyboard.append([__back_to_main_button])    
    return InlineKeyboardMarkup(keyboard)

# Generate a Keyboard of member search results
def get_member_listing_keyboard(results):
    _counter=0
    # Kerboard is a double List
    keyboard=[]
    _keyboard_rows=[]

    cols_per_row=2

    for _item in results:
        _counter += 1
        icon = ''

        # Head of Family
        if _item[4] == 1:
            icon += '⚡'
        # If Age and Gender data both are available
        #if _item[3] and _item[2]:
        if _item[3]:
            age = date.today().year - int(_item[3])
        else:
            age = None
        if age:
            if age <= 18:
                if _item[2] == 1:
                    icon += '👦🏻'
                elif _item[2] == 2:
                    icon += '👧🏻'
            elif age > 18:
                if _item[2] == 1:
                    icon += '🧔🏻'
                elif _item[2] == 2:
                    icon += '👩🏻'
        else:
            # No age data, check only Gender:
            if _item[2] == 1:
                icon += '♂'
            elif _item[2] == 2:
                icon += '♀'
        _keyboard_text=f"{icon} {_item[0]} ({_item[1][-5:-1]}) »"
        _keyboard_rows.append(
            InlineKeyboardButton(
                _keyboard_text, callback_data="Member_" + _item[1][-5:-1]
            )
        )
        # For every 2 cols in a row
        if _counter % cols_per_row == 0:
            # Add the rows to the main keyboard
            keyboard.append(_keyboard_rows)
            # Reinitialize the row
            _keyboard_rows=[]
    _keyboard_rows.append(__back_to_main_button)
    keyboard.append(_keyboard_rows)
    return InlineKeyboardMarkup(keyboard)