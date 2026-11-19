import os
import re
from datetime import date, datetime
from typing import cast

from pyrogram.enums import ButtonStyle
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputRichBlock,
    InputRichBlockButtons,
    InputRichBlockDetails,
    InputRichBlockFooter,
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichBlockTable,
    InputRichMessage,
    RichBlockTableCell,
    RichMessageButton,
    RichText,
    RichTextBold,
    RichTextButton,
    RichTextCode,
    RichTextEmailAddress,
    WebAppInfo,
)

from stoscbots.util import bot_auth
from stoscbots.xero import xero_utils

WEB_APP_PR = WebAppInfo(
    url="https://stosc.com/pr")


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
__STREAMING_GDRIVE_BUTTON = InlineKeyboardButton("📂 Google Drive Slides",
                                                 url="https://drive.google.com/drive/folders/13YnRvL9JZoGbeMXQ1T9E7vhaEZEFfUK8")
__STREAMING_LIVE_BUTTON = InlineKeyboardButton("▶️ Live Broadcast",
                                               url="https://stosc.com/live/")

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

back_to_members_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("← Back to Members", callback_data="Members Menu")]
])

back_to_my_details_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("← Back to My Details", callback_data="My Details Menu")]
])

dues_payment_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("💳 PayNow", callback_data="PayNow Menu")],
    [InlineKeyboardButton("← Back to My Details", callback_data="My Details Menu")],
])

back_to_prayer_groups_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("← Back to Prayer Groups", callback_data="Prayer Groups Menu")]
])

paynow_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("← Back to My Details", callback_data="My Details Menu")],
    [BACK_TO_MAIN_BUTTON],
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
    [BACK_TO_MAIN_BUTTON],
])

streaming_menu_keyboard = InlineKeyboardMarkup([
    [__STREAMING_GEN_ANNOUNCEMENT_SLIDES_BUTTON],
    [__STREAMING_GDRIVE_BUTTON, __STREAMING_LIVE_BUTTON],
    [BACK_TO_MAIN_BUTTON]
])

services_menu_keyboard = InlineKeyboardMarkup([
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


def _rich_button_row(*actions: tuple[str, str, ButtonStyle]) -> InputRichBlockButtons:
    return InputRichBlockButtons(
        buttons=[
            RichMessageButton(text=cast(RichText, label), callback_data=callback, style=style)
            for label, callback, style in actions
        ],
        align="left",
    )


def get_rich_main_menu(keyboard: InlineKeyboardMarkup) -> InputRichMessage:
    """Group the same role-filtered destinations used by the legacy keyboard."""
    available = {button.callback_data for row in keyboard.inline_keyboard for button in row}
    default = ButtonStyle.DEFAULT
    # Kurigram's rich-text serializer accepts strings and lists despite its annotations.
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "St. Thomas Orthodox Syrian Cathedral")),
            "\nSingapore · Member services",
            "\nFind a family by code: ",
            RichTextCode(cast(RichText, "/u A001")),
        ])),
        _rich_button_row(
            ("My details", "My Details Menu", ButtonStyle.PRIMARY),
            ("Members", "Members Menu", default),
            ("PayNow", "PayNow Menu", default),
        ),
        InputRichBlockDetails(
            summary=cast(RichText, "Community"),
            blocks=[_rich_button_row(
                ("Prayer groups", "Prayer Groups Menu", default),
                ("Harvest festival", "My Harvest Festival Menu", default),
            )],
            is_open=False,
        ),
    ]
    committee_actions = [
        (label, callback, default)
        for label, callback in (
            ("Services", "Services Menu"),
            ("Finance", "Finance Menu"),
            ("Streaming", "Streaming Menu"),
        )
        if callback in available
    ]
    committee_rows: list[InputRichBlock] = [_rich_button_row(*committee_actions)] if committee_actions else []
    if "Admin Menu" in available:
        committee_rows.append(_rich_button_row(("Admin", "Admin Menu", default)))
    if committee_rows:
        blocks.append(InputRichBlockDetails(
            summary=cast(RichText, "Committee tools"), blocks=committee_rows, is_open=False,
        ))
    blocks.append(InputRichBlockButtons(
        buttons=[
            RichMessageButton(text=cast(RichText, label), url=url, style=ButtonStyle.LINK)
            for label, url in (
                ("Church website", "https://stosc.com/"),
                ("Events", "https://stosc.com/calendar/"),
                ("Livestream", "https://stosc.com/live/"),
            )
        ],
        align="left",
    ))
    return InputRichMessage(blocks=blocks)


def get_rich_members_menu() -> InputRichMessage:
    default = ButtonStyle.DEFAULT
    return InputRichMessage(blocks=[
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Members")),
            "\nFind a family: ",
            RichTextCode(cast(RichText, "/u A001")),
            " (use a code or name).",
        ])),
        InputRichBlockParagraph(text=RichTextBold(cast(RichText, "Today’s celebrations"))),
        _rich_button_row(
            ("Birthdays today", "Member Birthday Today Button", ButtonStyle.PRIMARY),
            ("Anniversaries today", "Member Anniversary Today Button", default),
        ),
        InputRichBlockDetails(
            summary=cast(RichText, "This week"),
            blocks=[_rich_button_row(
                ("Birthdays this week", "Member Birthday Week Button", default),
                ("Anniversaries this week", "Member Anniversary Week Button", default),
            )],
            is_open=False,
        ),
        InputRichBlockDetails(
            summary=cast(RichText, "Church & membership"),
            blocks=[
                _rich_button_row(("New members · last 12 months", "New Members Button", default)),
                _rich_button_row(
                    ("Management committee", "MC", default),
                    ("General Body & quorum", "GB", default),
                ),
            ],
            is_open=False,
        ),
        _rich_button_row(("← Main menu", "Main Menu", ButtonStyle.LINK)),
    ])


def get_rich_prayer_groups_menu() -> InputRichMessage:
    return InputRichMessage(blocks=[
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Area Prayer Groups 🤲🏻")),
            "\nParish fellowship and local area communities across Singapore.",
            "\nSelect an area below to browse its directory:",
        ])),
    ])


def get_rich_my_details_menu() -> InputRichMessage:
    default = ButtonStyle.DEFAULT
    return InputRichMessage(blocks=[
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "My Details")),
            "\nYour church profile, contributions, and dues.",
        ])),
        _rich_button_row(
            ("🧾 My profile", "My Profile", ButtonStyle.PRIMARY),
        ),
        _rich_button_row(
            ("💳 Contributions", "My Contributions", default),
            ("📜 Dues", "My Dues", default),
        ),
        InputRichBlockDetails(
            summary=cast(RichText, "Church giving & services"),
            blocks=[
                _rich_button_row(("ℹ List of accounts", "List of Accounts", default)),
                InputRichBlockButtons(
                    buttons=[
                        RichMessageButton(
                            text=cast(RichText, "🙏 Submit prayer request"),
                            web_app=WEB_APP_PR,
                            style=default,
                        ),
                    ],
                    align="left",
                ),
            ],
            is_open=False,
        ),
        _rich_button_row(("← Main menu", "Main Menu", ButtonStyle.LINK)),
    ])


DEFAULT_PAYNOW_QR_PATH = os.path.join(os.path.dirname(__file__), "assets", "paynow_qr.jpg")
PAYNOW_QR_MEDIA = os.environ.get(
    "PAYNOW_QR_PATH",
    DEFAULT_PAYNOW_QR_PATH if os.path.exists(DEFAULT_PAYNOW_QR_PATH) else os.environ.get(
        "PAYNOW_QR_URL",
        "https://stosc.com/wp-content/uploads/2026/08/giving1.webp",
    ),
)
PAYNOW_QR_URL = PAYNOW_QR_MEDIA


def get_rich_paynow_menu(
    include_photo: bool = True,
    photo_media: str | None = None,
) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Payment Options 💵")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
        ])),
    ]
    if include_photo:
        media = photo_media or PAYNOW_QR_MEDIA
        blocks.append(InputRichBlockPhoto(photo=InputMediaPhoto(media)))

    blocks.extend([
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "1. PayNow (UEN)")),
            "\n• UEN: ", RichTextCode(cast(RichText, "S79SS0001L")), " (tap to copy)",
            "\n• Entity: St. Thomas Orthodox Syrian Cathedral",
            "\n\n",
            RichTextBold(cast(RichText, "2. Bank Transfer (DBS)")),
            "\n• Account: ", RichTextCode(cast(RichText, "0480155596")), " (tap to copy)",
            "\n• Bank: DBS Bank Ltd (Code: 7171, Branch: 048)",
            "\n• Name: St. Thomas Orthodox Syrian Cathedral",
            "\n\n",
            RichTextBold(cast(RichText, "3. Cash or Cheque")),
            "\n• Payable to: St. Thomas Orthodox Syrian Cathedral",
            "\n• Venue: Cathedral church office",
        ])),
        InputRichBlockDetails(
            summary=cast(RichText, "Reference & receipt guide"),
            blocks=[
                InputRichBlockParagraph(text=cast(RichText, [
                    RichTextBold(cast(RichText, "Payment Reference:")),
                    "\nPlease enter your family code and purpose in the transfer description (e.g. ",
                    RichTextCode(cast(RichText, "A001 Subscription")),
                    ").",
                    "\n\n",
                    RichTextBold(cast(RichText, "Multiple Contributions:")),
                    "\nFor combined transfers, email the itemized breakdown to ",
                    RichTextEmailAddress(text=cast(RichText, "accounts@stosc.com"), email_address="accounts@stosc.com"),
                    ".",
                ]))
            ],
            is_open=True,
        ),
    ])
    return InputRichMessage(blocks=blocks)


def _format_lot(code: object) -> str:
    try:
        return f"{int(code):03}"
    except (ValueError, TypeError):
        return str(code)


def get_rich_harvest_festival_menu(
    member_code: str | None = None,
    purchases_data: dict | None = None,
    contributions_data: dict | None = None,
    auction_portal_url: str | None = None,
) -> InputRichMessage:
    header_elements: list[object] = [
        RichTextBold(cast(RichText, "Harvest Festival 🌽")),
        "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
    ]
    if member_code:
        header_elements.extend(["\nMember: ", RichTextCode(cast(RichText, member_code))])

    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, header_elements)),
    ]

    if auction_portal_url:
        blocks.append(InputRichBlockButtons(
            buttons=[
                RichMessageButton(
                    text=cast(RichText, "🌐 Open Auction Portal"),
                    url=auction_portal_url,
                    style=ButtonStyle.LINK,
                )
            ],
            align="left",
        ))

    # Auction Wins section
    purchases_items = (purchases_data or {}).get("items") or []
    total_bid = (purchases_data or {}).get("total_bid", 0)

    if purchases_items:
        blocks.append(InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "🏆 Auction Wins")),
            f"\n{len(purchases_items)} item{'s' if len(purchases_items) != 1 else ''} won",
        ])))
        cells = [
            [
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Lot")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Item")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Won"))), align="right"),
            ]
        ]
        for item in purchases_items:
            lot = _format_lot(item.get("itemCode", ""))
            name = str(item.get("itemName", "Item"))
            bid_val = item.get("winning_bid", 0)
            try:
                bid_str = f"${float(bid_val):,.0f}"
            except (ValueError, TypeError):
                bid_str = f"${bid_val}"
            cells.append([
                RichBlockTableCell(text=cast(RichText, RichTextCode(cast(RichText, lot)))),
                RichBlockTableCell(text=cast(RichText, name)),
                RichBlockTableCell(text=cast(RichText, bid_str), align="right"),
            ])
        blocks.append(InputRichBlockTable(cells=cells, is_striped=True, is_compact=True))
        try:
            total_bid_str = f"${float(total_bid):,.0f}"
        except (ValueError, TypeError):
            total_bid_str = f"${total_bid}"
        blocks.append(InputRichBlockFooter(text=cast(RichText, f"Total Purchases: {total_bid_str}")))
    else:
        blocks.append(InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "🏆 Auction Wins")),
            "\n~ No bids or purchases yet ~",
        ])))

    # Donated Items (drawer)
    donated_items = (contributions_data or {}).get("items") or []
    total_fetched = (contributions_data or {}).get("total_fetched", 0)

    if donated_items:
        try:
            total_fetched_str = f"${float(total_fetched):,.0f}"
        except (ValueError, TypeError):
            total_fetched_str = f"${total_fetched}"

        summary = f"🎁 Donated Items ({len(donated_items)} item{'s' if len(donated_items) != 1 else ''} · {total_fetched_str})"
        d_cells = [
            [
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Lot")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Item")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Buyer")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Sold"))), align="right"),
            ]
        ]
        for d_item in donated_items:
            lot = _format_lot(d_item.get("itemCode", ""))
            name = str(d_item.get("itemName", "Item"))
            buyer = str(d_item.get("winner", "—"))
            bid_val = d_item.get("winning_bid", 0)
            try:
                sold_str = f"${float(bid_val):,.0f}"
            except (ValueError, TypeError):
                sold_str = f"${bid_val}"
            d_cells.append([
                RichBlockTableCell(text=cast(RichText, RichTextCode(cast(RichText, lot)))),
                RichBlockTableCell(text=cast(RichText, name)),
                RichBlockTableCell(text=cast(RichText, buyer)),
                RichBlockTableCell(text=cast(RichText, sold_str), align="right"),
            ])
        blocks.append(InputRichBlockDetails(
            summary=cast(RichText, summary),
            blocks=[
                InputRichBlockTable(cells=d_cells, is_striped=True, is_compact=True),
                InputRichBlockFooter(text=cast(RichText, f"Total raised for cathedral: {total_fetched_str}")),
            ],
            is_open=False,
        ))

    return InputRichMessage(blocks=blocks)


def get_rich_finance_menu() -> InputRichMessage:
    return InputRichMessage(blocks=[
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Church Finance & Accounts 💲")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
            "\nManagement Committee access only.",
            "\n\n",
            RichTextBold(cast(RichText, "Member Ledger Commands:")),
            "\n• ", RichTextCode(cast(RichText, "/x <CODE>")), " — View member contributions & payments",
            "\n• ", RichTextCode(cast(RichText, "/xs <CODE>")), " — View member invoices & dues",
            "\n(e.g. ", RichTextCode(cast(RichText, "/x A001")), ")",
        ])),
    ])


def get_rich_finance_bank_summary(report_rows: list[dict]) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Bank Accounts Summary 🏦")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
            "\nLive balances and YTD cash movements",
        ])),
    ]

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Account")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "In"))), align="right"),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Out"))), align="right"),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Closing"))), align="right"),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    all_fd_sum = 0.0
    total_closing = 0.0

    for row in report_rows:
        if row.get("RowType") == "Header":
            continue
        for bank_data in row.get("Rows", []):
            cells = bank_data.get("Cells", [])
            if len(cells) < 5:
                continue
            account_name = str(cells[0].get("Value", "Account"))
            closing_str = str(cells[4].get("Value") or "0")
            try:
                closing_val = float(closing_str)
            except (ValueError, TypeError):
                closing_val = 0.0

            if account_name.startswith("DBS FD"):
                all_fd_sum += closing_val
                continue

            try:
                in_val = float(cells[2].get("Value") or 0)
                in_str = f"${in_val:,.0f}" if in_val != 0 else "—"
            except (ValueError, TypeError):
                in_str = str(cells[2].get("Value", "—"))

            try:
                out_val = float(cells[3].get("Value") or 0)
                out_str = f"${out_val:,.0f}" if out_val != 0 else "—"
            except (ValueError, TypeError):
                out_str = str(cells[3].get("Value", "—"))

            if closing_val == 0.0 and in_str == "—" and out_str == "—":
                continue

            total_closing += closing_val

            table_cells.append([
                RichBlockTableCell(text=cast(RichText, account_name)),
                RichBlockTableCell(text=cast(RichText, in_str), align="right"),
                RichBlockTableCell(text=cast(RichText, out_str), align="right"),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, f"${closing_val:,.2f}"))), align="right"),
            ])

    if len(table_cells) > 1:
        blocks.append(InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True))

    footer_parts = [f"Fixed Deposits (DBS FD): ${all_fd_sum:,.2f}"]
    if total_closing > 0:
        footer_parts.append(f"Operating Total: ${total_closing:,.2f}")
    blocks.append(InputRichBlockFooter(text=cast(RichText, " · ".join(footer_parts))))

    return InputRichMessage(blocks=blocks)


def get_rich_finance_executive_summary(report_rows: list[dict]) -> InputRichMessage:
    current_month_title = "Current Month"
    previous_month_title = "Previous Month"

    filtered_rows = [
        row for row in report_rows
        if row.get("Title", "").upper() not in ["POSITION", "PERFORMANCE", "PROFITABILITY", "INCOME"]
    ]

    for row in filtered_rows:
        if row.get("RowType") == "Header":
            cells = row.get("Cells", [])
            if len(cells) > 2:
                current_month_title = str(cells[1].get("Value") or "Current Month")
                previous_month_title = str(cells[2].get("Value") or "Previous Month")

    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Financial Executive Summary 📊")),
            f"\nComparison: {current_month_title} vs {previous_month_title}",
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
        ])),
    ]

    first_section = True
    for row in filtered_rows:
        if row.get("RowType") == "Header":
            continue
        title = row.get("Title", "Section").title()
        section_items = row.get("Rows", [])
        if not section_items:
            continue

        s_cells = [
            [
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Metric")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, previous_month_title[:7]))), align="right"),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, current_month_title[:7]))), align="right"),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Var"))), align="right"),
            ]
        ]

        for s in section_items:
            cells = s.get("Cells", [])
            if len(cells) < 4:
                continue
            metric = str(cells[0].get("Value") or "")
            curr_raw = str(cells[1].get("Value") or "")
            prev_raw = str(cells[2].get("Value") or "")
            var_raw = str(cells[3].get("Value") or "")

            def _fmt(v: str) -> str:
                if not v or "%" in v:
                    return v or "—"
                try:
                    return f"${float(v):,.1f}"
                except (ValueError, TypeError):
                    return v

            var_arrow = "▼" if var_raw.startswith("-") else "▲" if var_raw else ""
            var_clean = var_raw.lstrip("-")
            var_display = f"{var_arrow}{var_clean}" if var_clean else "—"

            s_cells.append([
                RichBlockTableCell(text=cast(RichText, metric)),
                RichBlockTableCell(text=cast(RichText, _fmt(prev_raw)), align="right"),
                RichBlockTableCell(text=cast(RichText, _fmt(curr_raw)), align="right"),
                RichBlockTableCell(text=cast(RichText, var_display), align="right"),
            ])

        blocks.append(InputRichBlockDetails(
            summary=cast(RichText, f"📌 {title}"),
            blocks=[
                InputRichBlockTable(cells=s_cells, is_striped=True, is_compact=True),
            ],
            is_open=first_section,
        ))
        first_section = False

    return InputRichMessage(blocks=blocks)


def get_rich_finance_payments_wtd(payments_data: dict) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Invoice & Bill Payments (WTD) 💳")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
            "\nPast 7 days settlements",
        ])),
    ]

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Date")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Contact")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Type")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Amount"))), align="right"),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    total_rec = 0.0
    total_pay = 0.0
    count = 0

    for payment in (payments_data or {}).get("Payments", []):
        if payment.get("Status") == "DELETED":
            continue

        inv = payment.get("Invoice") or {}
        inv_type = inv.get("Type", "")
        is_pay = inv_type == "ACCPAY"
        icon = "🔸" if is_pay else "🔹"
        type_label = "Bill ⇨" if is_pay else "Receipt ⇦"

        date_val = payment.get("Date")
        if isinstance(date_val, datetime):
            _date = date_val
        else:
            try:
                _date = xero_utils.parse_Xero_Date(str(date_val))
            except Exception:
                _date = datetime.now()

        contact_name = str((inv.get("Contact") or {}).get("Name") or "Contact")
        raw_amt = payment.get("Amount", 0)
        try:
            amt_val = float(raw_amt)
        except (ValueError, TypeError):
            amt_val = 0.0

        if is_pay:
            total_pay += amt_val
        else:
            total_rec += amt_val
        count += 1

        date_str = f"{_date:%m-%d}"
        contact_display = f"{icon} {contact_name}"

        table_cells.append([
            RichBlockTableCell(text=cast(RichText, RichTextCode(cast(RichText, date_str)))),
            RichBlockTableCell(text=cast(RichText, contact_display)),
            RichBlockTableCell(text=cast(RichText, type_label)),
            RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, f"${amt_val:,.2f}"))), align="right"),
        ])

    if count > 0:
        blocks.append(InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True))
        blocks.append(InputRichBlockFooter(text=cast(
            RichText,
            f"🔹 Received: ${total_rec:,.2f} · 🔸 Paid: ${total_pay:,.2f}",
        )))
    else:
        blocks.append(InputRichBlockParagraph(text=cast(RichText, "~ No invoice or bill payments in the last 7 days ~")))

    return InputRichMessage(blocks=blocks)


def get_rich_finance_latest_tx(bank_tx_data: dict) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Latest Transactions (WTD) 🏦")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
            "\nCash, DBS & NETS movements (excluding invoices/bills)",
        ])),
    ]

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Date")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Contact")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Account")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Amount"))), align="right"),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    total_in = 0.0
    total_out = 0.0
    count = 0
    now = datetime.now()

    for tx in (bank_tx_data or {}).get("BankTransactions", []):
        date_val = tx.get("Date")
        if isinstance(date_val, datetime):
            tx_date = date_val
        else:
            try:
                tx_date = xero_utils.parse_Xero_Date(str(date_val))
            except Exception:
                tx_date = now

        if tx_date > now:
            continue

        tx_type = tx.get("Type", "")
        is_in = tx_type in {"RECEIVE", "RECEIVE-TRANSFER"}
        icon = "🔹" if is_in else "🔸" if tx_type in {"SPEND", "SPEND-TRANSFER"} else "❓"

        contact_name = str((tx.get("Contact") or {}).get("Name") or "General")

        acct_raw = str((tx.get("BankAccount") or {}).get("Name", "")).upper()
        if acct_raw == "CASH":
            acct_display = "💵 CASH"
        elif "DBS" in acct_raw:
            acct_display = "🏦 DBS"
        elif "NETS" in acct_raw:
            acct_display = "💳 NETS"
        else:
            acct_display = acct_raw[:8] if acct_raw else "Bank"

        raw_amt = tx.get("Total", 0)
        try:
            amt_val = float(raw_amt)
        except (ValueError, TypeError):
            amt_val = 0.0

        if is_in:
            total_in += amt_val
        else:
            total_out += amt_val
        count += 1

        date_str = f"{tx_date:%m-%d}"
        contact_display = f"{icon} {contact_name}"

        table_cells.append([
            RichBlockTableCell(text=cast(RichText, RichTextCode(cast(RichText, date_str)))),
            RichBlockTableCell(text=cast(RichText, contact_display)),
            RichBlockTableCell(text=cast(RichText, acct_display)),
            RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, f"${amt_val:,.2f}"))), align="right"),
        ])

    if count > 0:
        blocks.append(InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True))
        blocks.append(InputRichBlockFooter(text=cast(
            RichText,
            f"🔹 Inflow: ${total_in:,.2f} · 🔸 Outflow: ${total_out:,.2f}",
        )))
    else:
        blocks.append(InputRichBlockParagraph(text=cast(RichText, "~ No non-invoice transactions in the last 7 days ~")))

    return InputRichMessage(blocks=blocks)


def _get_trial_balance_section(report_rows: list[dict], is_income_report: bool) -> tuple[str, list[dict]]:
    target = "REVENUE" if is_income_report else "EXPENSE"
    for row in report_rows:
        if row.get("RowType") == "Section":
            title = str(row.get("Title") or "").upper()
            if target in title or (is_income_report and "INCOME" in title):
                return str(row.get("Title") or ("Revenue" if is_income_report else "Expense")), row.get("Rows", [])

    idx = 1 if is_income_report else 2
    if len(report_rows) > idx and report_rows[idx].get("RowType") == "Section":
        return str(report_rows[idx].get("Title") or ("Revenue" if is_income_report else "Expense")), report_rows[idx].get("Rows", [])

    if len(report_rows) > 1 and report_rows[1].get("RowType") == "Section":
        return str(report_rows[1].get("Title") or "Trial Balance"), report_rows[1].get("Rows", [])

    return ("Revenue" if is_income_report else "Expense"), []


def get_rich_finance_trial_balance(report_rows: list[dict], is_income_report: bool) -> InputRichMessage:
    year = datetime.now().year
    report_type_name = "Revenue" if is_income_report else "Expense"
    icon = "📈" if is_income_report else "📉"
    basis_note = "Cash basis (payments only)" if is_income_report else "Year-to-Date ledger"

    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, f"Trial Balance — {report_type_name} {icon}")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
            f"\nYear {year} · {basis_note}",
        ])),
    ]

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Account")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "YTD Amount"))), align="right"),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    val_index = 4 if is_income_report else 3
    _title, section_rows = _get_trial_balance_section(report_rows, is_income_report)

    calc_total = 0.0
    summary_total = None

    for row in section_rows:
        cells = row.get("Cells", [])
        if not cells or len(cells) <= val_index:
            continue
        name = str(cells[0].get("Value") or "").strip()
        if not name or row.get("RowType") == "Header":
            continue

        raw_val = cells[val_index].get("Value")
        try:
            amt = float(raw_val or 0)
        except (ValueError, TypeError):
            amt = 0.0

        if row.get("RowType") in ("SummaryRow", "Total") or name.lower().startswith("total"):
            summary_total = amt
            continue

        if amt == 0.0:
            continue

        calc_total += amt
        table_cells.append([
            RichBlockTableCell(text=cast(RichText, name)),
            RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, f"${amt:,.2f}"))), align="right"),
        ])

    final_total = summary_total if summary_total is not None else calc_total

    if len(table_cells) > 1:
        blocks.append(InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True))
        bullet = "🔹" if is_income_report else "🔸"
        blocks.append(InputRichBlockFooter(text=cast(
            RichText,
            f"{bullet} Total {report_type_name}: ${final_total:,.2f}",
        )))
    else:
        blocks.append(InputRichBlockParagraph(text=cast(RichText, f"~ No {report_type_name.lower()} account entries for Year {year} ~")))

    return InputRichMessage(blocks=blocks)


def get_member_finance_search_keyboard(member_code: str, year: str, current_view: str) -> InlineKeyboardMarkup:
    buttons = []
    if current_view == "payments":
        buttons.append(InlineKeyboardButton("📜 View Dues (/xs)", callback_data=f"search_xero_dues:{member_code}:{year}"))
    else:
        buttons.append(InlineKeyboardButton("💳 View Contributions (/x)", callback_data=f"search_xero_payments:{member_code}:{year}"))
    buttons.append(InlineKeyboardButton("👤 Family Profile", callback_data=f"related_family:{member_code}"))
    return InlineKeyboardMarkup([buttons])


def get_rich_member_payments(
    name: str,
    member_code: str,
    year: str,
    payments: list[dict],
) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Member Contributions 💳")),
            f"\n{name} (", RichTextCode(cast(RichText, member_code)), ")",
            f"\nYear {year} · Cathedral Parishioner Ledger",
        ])),
    ]

    if not payments:
        blocks.append(InputRichBlockParagraph(text=cast(
            RichText,
            f"~ No contributions recorded for {name} ({member_code}) in Year {year} ~",
        )))
        return InputRichMessage(blocks=blocks)

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Account")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Amount ($)"))), align="right"),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    total = 0.0
    for item in payments:
        account = str(item.get("Account") or "Contribution")
        raw_amt = item.get("LineAmount", 0)
        try:
            amt = float(raw_amt)
        except (ValueError, TypeError):
            amt = 0.0
        total += amt
        table_cells.append([
            RichBlockTableCell(text=cast(RichText, account)),
            RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, f"${amt:,.2f}"))), align="right"),
        ])

    blocks.append(InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True))

    latest_ts = max((item.get("modified_ts", "") for item in payments), default="")
    summary = f"🔹 Total Contributions: ${total:,.2f}"
    if latest_ts:
        summary += f" · As of {latest_ts[:16]}"
    blocks.append(InputRichBlockFooter(text=cast(RichText, summary)))

    return InputRichMessage(blocks=blocks)


def get_rich_member_invoices(
    name: str,
    member_code: str,
    year: str,
    invoices_data: dict,
) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Member Invoices & Dues 📜")),
            f"\n{name} (", RichTextCode(cast(RichText, member_code)), ")",
            f"\nYear {year} · Member Invoices Ledger",
        ])),
    ]

    all_invoices = (invoices_data or {}).get("Invoices", [])
    filtered: list[dict] = []
    for inv in all_invoices:
        if (
            inv.get("Type") == "ACCREC"
            and not str(inv.get("InvoiceNumber", "")).endswith("-VOID")
            and (
                str(inv.get("InvoiceNumber", "")).startswith(f"INV-{year[2:]}")
                or str(inv.get("InvoiceNumber", "")).startswith(f"HF-{year[2:]}")
                or (inv.get("Status") == "AUTHORISED" and int(str(inv.get("DateString", "0")).split("-")[0]) <= int(year))
            )
        ):
            filtered.append(inv)

    if not filtered:
        blocks.append(InputRichBlockParagraph(text=cast(
            RichText,
            f"~ No invoices found for {name} ({member_code}) in Year {year} ~",
        )))
        return InputRichMessage(blocks=blocks)

    due_invoices = [
        inv for inv in filtered
        if float(inv.get("AmountDue", 0)) > 0 or inv.get("Status") == "AUTHORISED"
    ]
    paid_invoices = [
        inv for inv in filtered
        if inv not in due_invoices
    ]

    total_due = sum(float(inv.get("AmountDue", 0)) for inv in due_invoices)
    total_paid = sum(float(inv.get("Total", 0)) for inv in paid_invoices)

    if due_invoices:
        due_cells = [
            [
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Invoice")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Description")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Due ($)"))), align="right"),
            ]
        ]
        for inv in due_invoices:
            inv_num = str(inv.get("InvoiceNumber") or "—")
            items = inv.get("LineItems") or []
            desc = ", ".join(l.get("Description", "") for l in items if l.get("Description")) or "Subscription"
            due_val = float(inv.get("AmountDue", 0))
            due_cells.append([
                RichBlockTableCell(text=cast(RichText, RichTextCode(cast(RichText, inv_num)))),
                RichBlockTableCell(text=cast(RichText, desc)),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, f"${due_val:,.2f}"))), align="right"),
            ])
        blocks.append(InputRichBlockTable(cells=due_cells, is_striped=True, is_compact=True))
    else:
        blocks.append(InputRichBlockParagraph(text=cast(
            RichText,
            f"🔹 All subscriptions and dues for Year {year} are fully settled!",
        )))

    if paid_invoices:
        paid_cells = [
            [
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Invoice")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Description")))),
                RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Paid ($)"))), align="right"),
            ]
        ]
        for inv in paid_invoices:
            inv_num = str(inv.get("InvoiceNumber") or "—")
            items = inv.get("LineItems") or []
            desc = ", ".join(l.get("Description", "") for l in items if l.get("Description")) or "Subscription"
            paid_val = float(inv.get("Total", 0))
            paid_cells.append([
                RichBlockTableCell(text=cast(RichText, RichTextCode(cast(RichText, inv_num)))),
                RichBlockTableCell(text=cast(RichText, desc)),
                RichBlockTableCell(text=cast(RichText, f"${paid_val:,.2f}"), align="right"),
            ])
        blocks.append(InputRichBlockDetails(
            summary=cast(RichText, f"📁 Settled Invoices ({len(paid_invoices)} paid · ${total_paid:,.2f})"),
            blocks=[InputRichBlockTable(cells=paid_cells, is_striped=True, is_compact=True)],
            is_open=len(due_invoices) == 0,
        ))

    footer_text = f"🔸 Total Due: ${total_due:,.2f} · 🔹 Total Settled: ${total_paid:,.2f}"
    blocks.append(InputRichBlockFooter(text=cast(RichText, footer_text)))

    return InputRichMessage(blocks=blocks)


def get_rich_streaming_menu() -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Cathedral Media & Streaming 📡")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
            "\nManagement Committee & Media Ministry tools.",
        ])),
        InputRichBlockDetails(
            summary=cast(RichText, "Announcement Slides & Media Guide"),
            blocks=[
                InputRichBlockParagraph(text=cast(RichText, [
                    RichTextBold(cast(RichText, "1. Weekly Announcement Slides 📺")),
                    "\nTap ", RichTextBold(cast(RichText, "Generate Announcement Slides")),
                    " below to build this week's slides. Processed slides are published directly to Google Drive.",
                    "\n\n",
                    RichTextBold(cast(RichText, "2. Photo & Flyer URL Generator 🖼")),
                    "\nSend any announcement flyer or photo directly to this bot chat. It will be uploaded to AWS S3, returning a public URL for announcements.",
                ])),
            ],
            is_open=True,
        ),
        InputRichBlockButtons(
            buttons=[
                RichMessageButton(
                    text=cast(RichText, "📂 Google Drive Slides"),
                    url="https://drive.google.com/drive/folders/13YnRvL9JZoGbeMXQ1T9E7vhaEZEFfUK8",
                    style=ButtonStyle.LINK,
                ),
                RichMessageButton(
                    text=cast(RichText, "▶️ Live Broadcast"),
                    url="https://stosc.com/live/",
                    style=ButtonStyle.LINK,
                ),
            ],
            align="left",
        ),
    ]
    return InputRichMessage(blocks=blocks)


def get_rich_slide_generation_result(is_linux: bool, returncode: int | None = None) -> InputRichMessage:
    if not is_linux:
        return InputRichMessage(blocks=[
            InputRichBlockParagraph(text=cast(RichText, [
                RichTextBold(cast(RichText, "Slide Generator Unavailable ⚠️")),
                "\nThis action is only available when STOSCBot runs in a Linux production environment.",
            ]))
        ])

    is_success = returncode == 0 if returncode is not None else True
    status_emoji = "✅" if is_success else "⚠️"
    status_text = "Announcement slides generated successfully!" if is_success else "Slides generation completed with non-zero status code."

    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, f"Announcement Slides Generation {status_emoji}")),
            f"\n{status_text}",
            "\n\nGenerated slides are synced to the Cathedral Google Drive folder.",
        ])),
        InputRichBlockButtons(
            buttons=[
                RichMessageButton(
                    text=cast(RichText, "📂 Open Google Drive"),
                    url="https://drive.google.com/drive/folders/13YnRvL9JZoGbeMXQ1T9E7vhaEZEFfUK8",
                    style=ButtonStyle.LINK,
                )
            ],
            align="left",
        ),
    ]
    return InputRichMessage(blocks=blocks)


def get_rich_services_menu() -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Cathedral Worship & Services ✝")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
            "\n114 Potong Pasir Ave 1, Singapore 358361",
        ])),
    ]

    schedule_cells = [
        [
            RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Service")))),
            RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Schedule")))),
        ],
        [
            RichBlockTableCell(text=cast(RichText, "Sunday Holy Qurbana")),
            RichBlockTableCell(text=cast(RichText, "8:00 AM (Matins) · 9:00 AM (Qurbana)")),
        ],
        [
            RichBlockTableCell(text=cast(RichText, "Saturday Evening Prayer")),
            RichBlockTableCell(text=cast(RichText, "6:30 PM (Sandhya Namaskaaram)")),
        ],
        [
            RichBlockTableCell(text=cast(RichText, "Wednesday Intercession")),
            RichBlockTableCell(text=cast(RichText, "7:30 PM (Cathedral & Online)")),
        ],
    ]

    blocks.extend([
        InputRichBlockTable(cells=schedule_cells, is_striped=True, is_compact=True),
        InputRichBlockDetails(
            summary=cast(RichText, "Liturgical Calendar & Prayer Requests"),
            blocks=[
                InputRichBlockParagraph(text=cast(RichText, [
                    RichTextBold(cast(RichText, "Liturgical Observances:")),
                    "\nFollow the Malankara Orthodox Syrian Church liturgical calendar, lectionary readings, feast days, and lenten schedules.",
                    "\n\n",
                    RichTextBold(cast(RichText, "Intercessory Prayer Requests:")),
                    "\nSubmit names for prayer remembrance during the Holy Qurbana (sick, departed, birthdays, anniversaries, thanksgiving) via the interactive prayer portal.",
                ])),
            ],
            is_open=False,
        ),
        InputRichBlockButtons(
            buttons=[
                RichMessageButton(
                    text=cast(RichText, "📜 Liturgical Calendar"),
                    url="https://stosc.com/calendar/",
                    style=ButtonStyle.LINK,
                ),
                RichMessageButton(
                    text=cast(RichText, "🙏 Prayer Request"),
                    url="https://stosc.com/pr",
                    style=ButtonStyle.LINK,
                ),
                RichMessageButton(
                    text=cast(RichText, "▶️ Live Broadcast"),
                    url="https://stosc.com/live/",
                    style=ButtonStyle.LINK,
                ),
            ],
            align="left",
        ),
        InputRichBlockFooter(text=cast(RichText, "vicar@stosc.com")),
    ])
    return InputRichMessage(blocks=blocks)


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


def format_search_parishioner_name(item) -> str:
    """Format member name for search results: strictly left-aligned names with right-side status indicators."""
    person_name = str(item[24] if len(item) > 24 and item[24] else "Member")
    is_head = len(item) > 23 and item[23] == 1

    is_kid = False
    if len(item) > 23 and item[23] == 3:
        is_kid = True
    elif len(item) > 20 and item[20]:
        try:
            year_str = str(item[20]).split("-")[0]
            if year_str.isdigit():
                age = date.today().year - int(year_str)
                if age <= 18:
                    is_kid = True
        except (ValueError, IndexError):
            pass

    if is_head:
        return f"{person_name} ⭐"
    if is_kid:
        return f"{person_name} 🎒"
    return person_name


def get_rich_member_search_results(query_str: str, results: list) -> InputRichMessage:
    count = len(results)
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Directory Search Results 🔎")),
            "\nQuery: ", RichTextCode(cast(RichText, query_str)),
            f" · Found {count} parishioner{'s' if count != 1 else ''}.",
        ])),
    ]

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Parishioner")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Code"))), align="center"),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    for item in results:
        fam_code = str(item[1] if len(item) > 1 and item[1] else "")
        person_id = str(item[25] if len(item) > 25 and item[25] else "")
        display_name = format_search_parishioner_name(item)

        # Tap person name to view member profile
        if person_id and fam_code:
            member_cell_text = RichTextButton(button=RichMessageButton(
                text=cast(RichText, display_name),
                style=ButtonStyle.LINK,
                callback_data=f"Member_{fam_code}_{person_id}",
            ))
        else:
            member_cell_text = cast(RichText, display_name)

        # Tap family code to view family profile
        if fam_code:
            code_cell_text = RichTextButton(button=RichMessageButton(
                text=cast(RichText, fam_code),
                style=ButtonStyle.LINK,
                callback_data=f"related_family:{fam_code.upper()}",
            ))
        else:
            code_cell_text = cast(RichText, "—")

        table_cells.append([
            RichBlockTableCell(text=cast(RichText, member_cell_text)),
            RichBlockTableCell(text=cast(RichText, code_cell_text), align="center"),
        ])

    blocks.extend([
        InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True),
        InputRichBlockFooter(text=cast(RichText, "⭐ Head of Family · 🎒 Student / Child\nTap any name to view profile, or code for family card.")),
    ])
    return InputRichMessage(blocks=blocks)


def get_rich_members_born_year(year: str, results: list) -> InputRichMessage:
    count = len(results)
    current_year = date.today().year
    try:
        age = current_year - int(year)
        age_str = f" · Turning {age} yrs in {current_year}" if age >= 0 else ""
    except ValueError:
        age_str = ""

    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, f"Members Born in {year} 🎂")),
            f"\nFound {count} registered parishioner{'s' if count != 1 else ''}{age_str}.",
        ])),
    ]

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Parishioner")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Birthday"))), align="center"),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Code"))), align="center"),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    for member in results:
        person_name = str(member[0] or "Member").strip()
        dob_str = str(member[1] or "").strip()
        fam_name = str(member[2] or "").strip()

        # Format birthday as e.g. "14 May"
        bday_display = dob_str
        try:
            parts = dob_str.split("-")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                bday_obj = date(2000, int(parts[1]), int(parts[2]))
                bday_display = f"{bday_obj.day} {bday_obj:%b}"
        except (ValueError, IndexError):
            pass

        # Extract family code if present
        fam_code_match = re.search(r"\(([A-Za-z][0-9]{3})\)", fam_name)
        fam_code = fam_code_match.group(1).upper() if fam_code_match else ""

        code_text = (
            RichTextButton(button=RichMessageButton(
                text=cast(RichText, fam_code),
                style=ButtonStyle.LINK,
                callback_data=f"related_family:{fam_code}",
            ))
            if fam_code else cast(RichText, "—")
        )

        table_cells.append([
            RichBlockTableCell(text=cast(RichText, person_name)),
            RichBlockTableCell(text=cast(RichText, bday_display), align="center"),
            RichBlockTableCell(text=cast(RichText, code_text), align="center"),
        ])

    blocks.extend([
        InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True),
        InputRichBlockFooter(text=cast(RichText, "Tap a family code to view the household profile.")),
    ])
    return InputRichMessage(blocks=blocks)


def get_rich_version_card(version_info: dict, runtime_info: dict) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "STOSCBot Version & Runtime 🤖")),
            "\nSt. Thomas Orthodox Syrian Cathedral, Singapore",
        ])),
    ]

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Attribute")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Details")))),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    rows = [
        ("Release Version", version_info.get("version", "Unknown")),
        ("Release Date", version_info.get("release_date", "Unknown")),
        ("Build SHA", version_info.get("build", "Unknown")),
        ("Git Branch", version_info.get("branch", "Unknown")),
        ("Telegram Runtime", str(runtime_info.get("app_version", "Unknown"))),
        ("Python Engine", str(runtime_info.get("python_version", "Unknown"))),
        ("Bot Session", str(runtime_info.get("session_name", "stoscbot"))),
    ]

    for label, val in rows:
        table_cells.append([
            RichBlockTableCell(text=cast(RichText, label)),
            RichBlockTableCell(text=cast(RichText, RichTextCode(cast(RichText, val)))),
        ])

    blocks.extend([
        InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True),
        InputRichBlockFooter(text=cast(RichText, "Singapore Standard Time (UTC+8) · Production Bot")),
    ])
    return InputRichMessage(blocks=blocks)


def get_rich_admin_menu() -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Cathedral Developer & Admin Hub 🛠")),
            "\nSystem telemetry, diagnostic utilities, and audit tools for Super Administrators.",
        ])),
        InputRichBlockDetails(
            summary=cast(RichText, "CLI Commands Quick Reference"),
            blocks=[
                InputRichBlockParagraph(text=cast(RichText, [
                    RichTextBold(cast(RichText, "Available Super Admin Commands:\n")),
                    "• ", RichTextCode(cast(RichText, "/cmd logs [filter]")), " - Tail audit logs with optional filter\n",
                    "• ", RichTextCode(cast(RichText, "/id [member_code]")), " - Lookup Telegram ID from Member Code\n",
                    "• ", RichTextCode(cast(RichText, "/add [tg_id] [code] [name]")), " - Register user Telegram ID\n",
                    "• ", RichTextCode(cast(RichText, "/send [id|ALL] [msg]")), " - Broadcast message to recent users\n",
                    "• ", RichTextCode(cast(RichText, "/version")), " - Display bot version and runtime stats",
                ])),
            ],
            is_open=False,
        ),
        InputRichBlockFooter(text=cast(RichText, "Confidential · Authorized super admin access only")),
    ]
    return InputRichMessage(blocks=blocks)


def get_rich_admin_stats(month_name: str, cmd_result: str, host_supported: bool = True) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, "Top Active Parishioners 📊")),
            f"\nAudit Period: {month_name} · Top users by message volume",
        ])),
    ]

    if not host_supported:
        blocks.append(InputRichBlockParagraph(text=cast(RichText, "⚠️ Telemetry log analysis is only available on the Linux production host.")))
        blocks.append(InputRichBlockFooter(text=cast(RichText, "Audit telemetry · St. Thomas Orthodox Syrian Cathedral")))
        return InputRichMessage(blocks=blocks)

    lines = [line.strip() for line in cmd_result.strip().splitlines() if line.strip()]
    if not lines:
        blocks.append(InputRichBlockParagraph(text=cast(RichText, "~ No user activity telemetry recorded for this month ~")))
        blocks.append(InputRichBlockFooter(text=cast(RichText, "Audit telemetry · St. Thomas Orthodox Syrian Cathedral")))
        return InputRichMessage(blocks=blocks)

    header_cells = [
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Rank"))), align="center"),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Parishioner")))),
        RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, "Messages"))), align="right"),
    ]
    table_cells: list[list[RichBlockTableCell]] = [header_cells]

    total_msgs = 0
    for idx, line in enumerate(lines, start=1):
        parts = line.split(maxsplit=1)
        count_str = parts[0] if len(parts) >= 1 else "0"
        name_str = parts[1] if len(parts) >= 2 else "Unknown"
        if count_str.isdigit():
            total_msgs += int(count_str)

        table_cells.append([
            RichBlockTableCell(text=cast(RichText, f"#{idx}"), align="center"),
            RichBlockTableCell(text=cast(RichText, name_str)),
            RichBlockTableCell(text=cast(RichText, RichTextBold(cast(RichText, count_str))), align="right"),
        ])

    blocks.extend([
        InputRichBlockTable(cells=table_cells, is_striped=True, is_compact=True),
        InputRichBlockFooter(text=cast(RichText, f"Total messages from top users: {total_msgs:,}")),
    ])
    return InputRichMessage(blocks=blocks)


def get_rich_admin_logs(title: str, log_text: str, is_error: bool = False) -> InputRichMessage:
    blocks: list[InputRichBlock] = [
        InputRichBlockParagraph(text=cast(RichText, [
            RichTextBold(cast(RichText, title)),
            f"\nHost: Linux · {'Error diagnostics' if is_error else 'Activity telemetry'}",
        ])),
    ]

    cleaned_text = log_text.strip()
    if not cleaned_text:
        blocks.append(InputRichBlockParagraph(text=cast(RichText, "~ No matching log entries found ~")))
    else:
        # Cap log text length to prevent exceeding Telegram block limits
        if len(cleaned_text) > 3000:
            cleaned_text = cleaned_text[-3000:]
        blocks.append(InputRichBlockParagraph(text=cast(RichText, RichTextCode(cast(RichText, cleaned_text)))))

    blocks.append(InputRichBlockFooter(text=cast(RichText, f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} SGT")))
    return InputRichMessage(blocks=blocks)


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
