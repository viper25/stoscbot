from multiprocessing.connection import Client
import os
import boto3
import requests
import re
from datetime import date
import datetime
from datetime import timedelta
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup
from boto3.dynamodb.conditions import Key
from stoscbots.xero import xero_utils
from stoscbots.util.loggers import LOGLEVEL
import logging
import pickle

# ----------------------------------------------------------------------------------------------------------------------
# Module logger
logger = logging.getLogger('Utils')
logger.setLevel(LOGLEVEL)
# ----------------------------------------------------------------------------------------------------------------------
resource = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ.get("STOSC_DDB_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("STOSC_DDB_SECRET_ACCESS_KEY"),
    region_name="ap-southeast-1",
)
table_stosc_bot_member_telegram = resource.Table('stosc_bot_member_telegram')
table_member_payments = resource.Table('stosc_xero_member_payments')

table_harvest_metrics = resource.Table('stosc_harvest_metrics')
table_stosc_harvest_winners = resource.Table('stosc_harvest_winners')
table_stosc_harvest_contributors = resource.Table('stosc_harvest_contributors')

table_harvest_items = resource.Table("stosc_harvest_items")
table_harvest_members = resource.Table("stosc_harvest_members")
table_stosc_xero_accounts_tracking = resource.Table("stosc_xero_accounts_tracking")
table_stosc_xero_tokens = resource.Table("stosc_xero_tokens")

# ----------------------------------------------------------------------------------------------------------------------
# get Telegram ID from STOSC Member code
def get_TelegramID_from_MemberCode(member_code: str):
    # Get the code from DynamoDB from the secondary index member_code-index
    response = table_stosc_bot_member_telegram.query(IndexName='member_code-index', KeyConditionExpression=Key('member_code').eq(member_code.upper()))
    if len(response['Items']) > 0:
        return response['Items']

# ----------------------------------------------------------------------------------------------------------------------
# get STOSC Member code from Telegram ID
def getMemberCode_from_TelegramID(telegram_id: int):
    response = table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        return response['Items'][0]['member_code']


# ----------------------------------------------------------------------------------------------------------------------
def get_address_details(_zip: str):
    try:
        result = requests.get(
            f'https://developers.onemap.sg//commonapi/search?searchVal={_zip}&returnGeom=Y&getAddrDetails=Y').json()
        if len(result['results']) > 0:
            return result['results'][0]['LATITUDE'], result['results'][0]['LONGITUDE']
    except Exception as e:
        logger.error(f"Exception in onemap API: {e}")


# ----------------------------------------------------------------------------------------------------------------------
# Generate a Member Profile msg
def generate_profile_msg_for_family(result: list) -> str:
    """Generate a profile message for a family based on the given result."""
    # Helper function to format the message
    def format_msg(label: str, value: str, index: int, link: bool = False) -> str:
        if value and value != "":
            if link:
                return f"• {label}: [{value}](tel://{value})\n"
            else:
                return f"• {label}: **{value}**\n"
        return ""

    # Extract the first row from the result
    row = result[0]

    # Start with the family name and head
    msg = f"• Family: **{row[2]} ({row[1]})**\n"

    # Add other details
    msg += format_msg("DOB", row[20], 20)
    msg += format_msg("Spouse", row[6], 6)
    msg += format_msg("Spouse DOB", row[21], 21)
    msg += format_msg("Children", row[8], 8)
    msg += format_msg("Other family members", row[9], 9)

    # Handle address concatenation
    address_parts = [row[i] for i in range(10, 13) if row[i] and row[i] != ""]
    if address_parts:
        msg += "• Add: " + ", ".join([f"**{part}**" for part in address_parts]) + "\n"

    # Add contact details
    msg += format_msg("Mobile", row[13], 13, link=True)
    msg += format_msg("Home", row[14], 14, link=True)
    msg += format_msg("Email", row[3], 3)
    if row[7] and row[7] != "" and row[7] != row[5]:
        msg += format_msg("Spouse Email", row[7], 7)

    # Add other details
    msg += format_msg("Home Parish", row[15], 15)
    msg += format_msg("Membership Date", row[16], 16)
    msg += format_msg("Related Families", row[17], 17)
    msg += format_msg("Electoral Roll", row[18], 18)
    msg += format_msg("Prayer Group", row[19], 19)

    return msg


# ----------------------------------------------------------------------------------------------------------------------
# This method can be called from a Telegram button or command such as /x V019
def generate_msg_xero_member_payments(name: str, _member_code: str, _year: str):
    payments = get_member_payments(_member_code, _year)
    if payments:
        msg = f"**{name}**\n`For Year {_year}`\n"
        msg += "➖➖➖➖➖➖➖\n"
        if len(payments) == 0:
            msg += "No payments yet"
        latest_ts = ''
        for item in payments:
            msg += f"► {item['Account']}: **${str(item['LineAmount'])}**\n"
            latest_ts = item['modfied_ts'] if (item['modfied_ts'] > latest_ts) else latest_ts
        if latest_ts != '':
            msg += f"\n`As of: {latest_ts[:16]}`"
        return msg
    return f"No contributions for **{name}** for year **{_year}**"


# ----------------------------------------------------------------------------------------------------------------------
# Return a list of member payments for a year
def get_member_payments(_member_code: str, _year: str) -> list:
    xero_contactID = xero_utils.get_xero_ContactID(_member_code)
    if xero_contactID is not None:
        response = table_member_payments.query(
            KeyConditionExpression=Key('ContactID').eq(xero_contactID) & Key('AccountCode').begins_with(_year))
    else:
        return None
    return response['Items']


# ----------------------------------------------------------------------------------------------------------------------
# This method can be called from a Telegram button or command such as /xs V019
# Returns a list of all Invoices paid and due for a member
def generate_msg_xero_member_invoices(_member_code: str, _year: str):
    if not is_valid_year(_year):
        return f"Not a valid year: **{_year}**"
    _invoices = xero_utils.get_Invoices(_member_code)
    if _invoices and len(_invoices['Invoices']) > 0:
        msg = f"--**{_invoices['Invoices'][0]['Contact']['Name']} ({_member_code})**--\n\n"
        icon = '🟠'
        for invoice in _invoices["Invoices"]:
            if (
                    # Show only Invoices and not Bills
                    invoice["Type"] == "ACCREC"
                    # Don't show VOID invoices
                    and not invoice["InvoiceNumber"].endswith("-VOID")
                    and (
                    # Show only invoices that are INV-<year> or HF-<year> or created in <year> or status = AUTHORIZED
                    invoice["InvoiceNumber"].startswith(f"INV-{_year[2:]}")
                    or invoice["InvoiceNumber"].startswith(f"HF-{_year[2:]}")  # Show all pending invoices upto <year>
                    or (invoice["Status"] == "AUTHORISED" and int(invoice["DateString"].split("-")[0]) <= int(_year))
            )
            ):
                if invoice["InvoiceNumber"].endswith("-VOID"):
                    # Skip invoices that were VOIDED. These have a -VOID at the end
                    continue
                logger.debug(f"Invoice No: {invoice['InvoiceNumber']} for amount: {invoice['AmountDue']}")
                if invoice["Status"] == "PAID":
                    icon = "🟢"
                elif invoice["Status"] == "AUTHORISED":
                    invoice["Status"] = "DUE"
                    icon = "🟠"
                elif invoice["Status"] == "VOIDED":
                    # Don't show VOIDED invoices
                    continue
                elif invoice["Status"] == "DRAFT":
                    icon = "🟠"
                elif invoice["Status"] == "DELETED":
                    # Don't show DELETED invoices
                    continue
                msg += (
                    f"**[{invoice['InvoiceNumber']}] - **"
                    if (invoice["InvoiceNumber"] != "" and invoice["InvoiceNumber"] is not None)
                    else "[`-NA-`] - "
                )
                # For a neater display
                if invoice["AmountDue"] == 0 or invoice["AmountDue"] == invoice["Total"]:
                    msg += f"**${invoice['Total']:,.2f}**: {invoice['Status']} {icon}\n"
                else:
                    msg += f"**${invoice['Total']:,.2f}**: ${invoice['AmountDue']:,.2f} {invoice['Status']} {icon}\n"
                for line in invoice["LineItems"]:
                    # msg += "−−−−\n"
                    msg += f"  `{line['Description']}-${line['LineAmount']:,.2f}`\n"
                # &curren is interpreted as ¤. So encode the ampersand sign
                # if invoice['AmountDue'] > 0:
                #     msg += f"**[(PayNow link)](https://stosc.com/paynow/?invoiceNo={invoice['InvoiceNumber']}&amp;currency=SGD&amount={invoice['AmountDue']}&shortCode=!wL!x0)**\n"
                msg += "––––————————————————\n"
        return msg
    return f"No invoices for {_member_code}"


# ----------------------------------------------------------------------------------------------------------------------
# Send a message to a Telegram user with an optional inline keyboard
async def edit_and_send_msg(query: CallbackQuery, msg: str, keyboard: InlineKeyboardMarkup = None):
    try:
        await query.message.edit_text(text=msg, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        if e.ID == 'MESSAGE_NOT_MODIFIED':
            logger.warn(e.MESSAGE)
        else:
            logger.error(e.MESSAGE)


# ----------------------------------------------------------------------------------------------------------------------
# Return Jan 1 of current year. For Xero accounting methods
def year_start():
    return date(date.today().year, 1, 1).strftime("%Y-%m-%d") \
        # ----------------------------------------------------------------------------------------------------------------------


# Return the start of the week (from Sunday 7.45 AM onwards)
def week_start_from_service_time():
    # Set to Sunday at current time
    start_of_week = datetime.datetime.today() - timedelta(days=datetime.datetime.today().weekday() + 1)
    # Set to 7.45 AM (because we start accepting new prayers at 7.45 AM)
    return start_of_week.replace(hour=7, minute=45)


# ----------------------------------------------------------------------------------------------------------------------
# # Return current date
def todays_date():
    return date.today().strftime("%Y-%m-%d")


# ----------------------------------------------------------------------------------------------------------------------
# Return date a week ago
def a_week_ago():
    return datetime.datetime.today() - timedelta(days=7)


# ----------------------------------------------------------------------------------------------------------------------
def get_member_auction_link(_member_code: str) -> str:
    response = table_harvest_members.query(KeyConditionExpression=Key("code").eq(_member_code))
    if response['Items']:
        return f"https://harvest.stosc.com/?id={response['Items'][0]['guid']}"
    else:
        return ""


# ----------------------------------------------------------------------------------------------------------------------
def generate_msg_member_auction_contributions(_member_code: str):
    try:
        response = table_stosc_harvest_contributors.query(KeyConditionExpression=Key("member_code").eq(_member_code))
    except Exception as e:
        logger.error(e)
        return None
    if len(response['Items']) > 0:
        msg = f"**Auction Donations**\n"
        msg += "➖➖➖➖➖➖➖\n"
        msg += f"Items Donated: {len(response['Items'][0]['items'])}\n"
        msg += "———————\n"
        for _item in response['Items'][0]['items']:
            msg += f"[`{_item['itemCode']:03}`] **{_item['itemName']}**: {_item['winner']} (${_item['winning_bid']:,}) ({_item['bids']} bids)\n"
        msg += "———————\n"
        msg += f"Total sold for: **${response['Items'][0]['total_fetched']:,}**\n"
        return msg
    else:
        return None


# ----------------------------------------------------------------------------------------------------------------------
def generate_msg_member_auction_purchases(_member_code: str):
    try:
        response = table_stosc_harvest_winners.query(KeyConditionExpression=Key("member_code").eq(_member_code))
    except Exception as e:
        logger.error(e)
        return "No Data"
    if len(response['Items']) > 0:
        if len(response['Items'][0]['items']) != 0:
            msg = f"**Auction Wins**\n"
            msg += "➖➖➖➖➖➖➖\n"
            if len(response['Items'][0]['items']) > 0:
                msg += f"Items Won: {len(response['Items'][0]['items'])}\n"
                msg += "———————\n"
                for _item in response['Items'][0]['items']:
                    msg += f"[`{_item['itemCode']:03}`] **{_item['itemName']}**: ${_item['winning_bid']:,} ({_item['bids']} bids)\n"
            msg += "———————\n"
            msg += f"Total: **${response['Items'][0]['total_bid']:,}**\n"
    else:
        msg = "~ No bids or purchases yet ~\n"
    return msg


# ----------------------------------------------------------------------------------------------------------------------
async def send_profile_address_and_pic(client: Client, _x: CallbackQuery, msg: str, result: list,
                                       searched_person: str = None, searched_person_name: str = None,
                                       keyboard: InlineKeyboardMarkup = None):
    # Send if there's a Zip code present and if Family code is searched for
    # Don't map send for person searches
    if (result[0][12] != "" and result[0][12] is not None and searched_person is None):
        if get_address_details(result[0][12]):
            lat, lon = get_address_details(result[0][12])
            await client.send_venue(chat_id=_x.from_user.id, latitude=float(lat), longitude=float(lon),
                                    title=result[0][2], address=result[0][10], disable_notification=True)
    try:
        # All images are png, so try looking that up first. Adding parameter to the URL to avoid stale cache 
        if searched_person:
            person_pic_caption = f"{searched_person_name} `({result[0][1]})`"
            await client.send_photo(chat_id=_x.from_user.id,
                                    photo=f"https://crm.stosc.com/churchcrm/Images/Person/{searched_person}.png?rand={hash(datetime.datetime.today())}",
                                    caption=person_pic_caption + "\n\n" + msg)
        # Send family pic only for searches by member code
        if searched_person is None:
            await client.send_photo(chat_id=_x.from_user.id,
                                    photo=f"https://crm.stosc.com/churchcrm/Images/Family/{result[0][0]}.png?rand={hash(datetime.datetime.today())}",
                                    caption=msg, reply_markup=keyboard)
    except Exception as e1:
        if e1.ID == 'MEDIA_EMPTY':
            logger.warn(f"No png image for [{result[0][1]}], trying jpg")
        else:
            logger.error(f"{e1.MESSAGE}: for [{result[0][1]}]")
        try:
            # If no png, try looking for a jpg
            if searched_person:
                person_pic_caption = f"{searched_person_name} `({result[0][1]})`"
                await client.send_photo(chat_id=_x.from_user.id,
                                        photo=f"https://crm.stosc.com/churchcrm/Images/Person/{searched_person}.jpg?rand={hash(datetime.datetime.today())}",
                                        caption=person_pic_caption)
            await client.send_photo(chat_id=_x.from_user.id,
                                    photo=f"https://crm.stosc.com/churchcrm/Images/Family/{result[0][0]}.jpg?rand={hash(datetime.datetime.today())}",
                                    caption=msg, reply_markup=keyboard)
        except Exception as e2:
            if e2.ID == 'MEDIA_EMPTY':
                logger.warn(f"No png or jpg image for [{result[0][1]}]")
                # No Image found, send details without photo then
                await client.send_message(chat_id=_x.from_user.id, text=msg, reply_markup=keyboard)
            else:
                logger.error(f"{e2.MESSAGE}: for [{result[0][1]}]")
                await client.send_message(chat_id=_x.from_user.id, text=msg, reply_markup=keyboard)


# ----------------------------------------------------------------------------------------------------------------------
def is_valid_member_code(member_code: str) -> bool:
    if not member_code:
        return False
    if len(member_code) != 4:
        return False
    if not re.match(r'[A-Za-z]\d{3}', member_code):
        return False
    return True


# ----------------------------------------------------------------------------------------------------------------------
def is_valid_year(year: str):
    """
    Check if a given string is a valid year.

    Args:
        year (str): A string representing the year.

    Returns:
        bool: True if the year is valid, False otherwise.
    """
    if len(year) != 4:
        return False

    if re.match(r"\d{4}", year) is None:
        return False

    return True


# ----------------------------------------------------------------------------------------------------------------------
def get_tracked_projects(raw_data: bool = False):
    response = table_stosc_xero_accounts_tracking.scan()

    # Get the latest modified_ts for all the projects
    last_updated = max(response['Items'], key=lambda x: x.get('modified_ts', '0'))['modified_ts']

    if raw_data:
        return response["Items"]

    msg = "**TRACKED PROJECTS**\n"
    msg += "➖➖➖➖➖➖➖➖\n"

    for _item in response["Items"]:
        income = _item.get('income', 0.0)
        expense = _item.get('expense', 0.0)

        if income or expense:
            msg += f"• {_item['Name']} - `${income:,.2f}` | `${expense:,.2f}`\n"

    msg += f"\n`As of: {last_updated}`"
    return msg


# ----------------------------------------------------------------------------------------------------------------------
def get_outstandings():
    msg = "**OUTSTANDING DUES**\n"
    msg += "➖➖➖➖➖➖➖➖\n\n"
    if os.environ.get("ENV") == 'TEST':
        filehandler = open("C:\\DATA\\git\\viper25\\xero_helpers\\outstandings.pickle", 'rb')
    else:
        filehandler = open(os.environ.get("OUTSTANDING_PICKLE_PATH"), 'rb')
    df = pickle.load(filehandler)
    msg = df.to_markdown()
    msg = f"`{msg}`"
    return msg


# ----------------------------------------------------------------------------------------------------------------------
def is_valid_email(email: str):
    if not email:
        return False
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    return True
