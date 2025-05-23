import datetime
import logging
import os
import pickle
import re
from datetime import date
from datetime import timedelta
from multiprocessing.connection import Client
from typing import Optional

import boto3
import requests
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified, BadRequest
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup

from stoscbots.util.loggers import LOGLEVEL
from stoscbots.xero import xero_utils

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
def get_TelegramID_from_MemberCode(member_code: str):
    """
    Fetches the Telegram ID associated with a given member code from DynamoDB.

    Args:
    - member_code (str): The member code to search for.

    Returns:
    - dict: The item from DynamoDB if found, otherwise None.
    """
    try:
        response = table_stosc_bot_member_telegram.query(
            IndexName='member_code-index',
            KeyConditionExpression=Key('member_code').eq(member_code.upper())
        )

        # Return the first item if found, otherwise return None.
        return response['Items'][0] if response['Items'] else None

    except Exception as e:
        print(f"Error fetching Telegram ID for member code {member_code}: {e}")
        return None


# ----------------------------------------------------------------------------------------------------------------------
# get STOSC Member code from Telegram ID
def getMemberCode_from_TelegramID(telegram_id: int):
    response = table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        return response['Items'][0]['member_code']


# ----------------------------------------------------------------------------------------------------------------------
def get_address_details(_zip: str):
    try:
        # https://www.onemap.gov.sg/apidocs/apidocs/#search
        url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={_zip}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
        result = requests.get(url).json()
        if len(result['results']) > 0:
            return result['results'][0]['LATITUDE'], result['results'][0]['LONGITUDE']
    except Exception as e:
        logger.error(f"Exception in onemap API: {e}")


# ----------------------------------------------------------------------------------------------------------------------
# Generate a Member Profile msg
def generate_profile_msg_for_family(result: list) -> str:
    """Generate a profile message for a family based on the given result."""

    row = result[0]
    msg = ""

    # Check if target_per_ID is present (indicating 'code' search result)
    # Indices 22-29 are for target person
    if len(row) >= 30 and row[24] is not None and str(row[24]).strip() != "":
        target_id_val = str(row[24]).strip()
        target_fullname_val = str(row[25]).strip()
        fmr_id_val = row[23] 
        target_dob_val = str(row[26]).strip() if row[26] else None
        target_email_val = str(row[27]).strip() if row[27] else None
        target_cellphone_val = str(row[28]).strip() if row[28] else None
        target_homephone_val = str(row[29]).strip() if row[29] else None

        role_map = {1: 'Head of Family', 2: 'Spouse', 3: 'Child', 7: 'Other Family Member'}
        role_str_val = role_map.get(fmr_id_val, 'Member')

        msg += "**Searched Person:**\n"
        msg += f"• Name: **{target_fullname_val}** ({target_id_val})\n"
        msg += f"• Role: **{role_str_val}**\n"
        if target_dob_val and target_dob_val.lower() != 'null' and target_dob_val.strip() != '//':
            msg += f"• DOB: **{target_dob_val}**\n"
        if target_email_val and target_email_val.lower() != 'null':
            msg += f"• Email: **{target_email_val}**\n"
        
        if target_cellphone_val and target_cellphone_val.lower() != 'null':
            clean_cell_digits = re.sub(r'\D', '', target_cellphone_val) # Get only digits
            display_cell = target_cellphone_val
            if not display_cell.startswith('+') and clean_cell_digits: # Add + if not present for display
                 display_cell = f"+{target_cellphone_val}"

            link_cell = clean_cell_digits
            if re.match(r"^(65)?(6|8|9)\d{7}$", clean_cell_digits): # SG Number
                 link_cell = "65" + clean_cell_digits[-8:] # Ensure 65 prefix for link
            
            if link_cell: # Only add if we have a linkable number
                msg += f"• Mobile: [{display_cell}](https://wa.me/{link_cell})\n"

        if target_homephone_val and target_homephone_val.lower() != 'null':
            clean_home_digits = target_homephone_val.replace(' ', '').replace('-', '')
            if clean_home_digits:
                msg += f"• Home: [{target_homephone_val}](tel://{clean_home_digits})\n"
        msg += "\n**Family Details:**\n"

    # Helper function to format the message for family details
    def format_family_msg(label: str, value: Optional[str], link_type: Optional[str] = None) -> str:
        if value is not None and str(value).strip() != "" and str(value).strip().lower() != 'null' and str(value).strip() != '//':
            val_str = str(value).strip()
            if link_type == "tel":
                clean_val_digits = val_str.replace(' ', '').replace('-', '')
                if clean_val_digits:
                    return f"• {label}: [{val_str}](tel://{clean_val_digits})\n"
            elif link_type == "wa":
                clean_val_digits = re.sub(r'\D', '', val_str) # Get only digits
                display_val = val_str
                if not display_val.startswith('+') and clean_val_digits: # Add + if not present for display
                    display_val = f"+{val_str}"
                
                link_val_digits = clean_val_digits
                if re.match(r"^(65)?(6|8|9)\d{7}$", clean_val_digits): # SG Number
                    link_val_digits = "65" + clean_val_digits[-8:] # Ensure 65 prefix for link
                elif clean_val_digits.startswith('+'): # If original had +, remove for link path
                    link_val_digits = clean_val_digits[1:]

                if link_val_digits: # Only add if we have a linkable number
                    return f"• {label}: [{display_val}](https://wa.me/{link_val_digits})\n"
            else:
                return f"• {label}: **{val_str}**\n"
        return ""

    # Family Details Section (Indices 0-21 primarily)
    msg += format_family_msg(f"Family: **{row[2]} ({row[1]})**", None) # Special case for first line, no label before **

    # Husband (Head) and Wife (Spouse) details
    husband_name = str(row[4]) if row[4] else None
    husband_dob = str(row[20]) if row[20] else None
    wife_name = str(row[6]) if row[6] else None
    wife_dob = str(row[21]) if row[21] else None

    if husband_name and husband_name.strip() != "" and husband_name.lower() != 'null':
        msg += format_family_msg("Head", husband_name)
        if husband_dob and husband_dob.strip() != "" and husband_dob.lower() != 'null' and husband_dob.strip() != '//':
            msg += format_family_msg("  DOB", husband_dob)
    elif husband_dob and husband_dob.strip() != "" and husband_dob.lower() != 'null' and husband_dob.strip() != '//': # Only DOB for Head
        msg += format_family_msg("Head DOB", husband_dob)

    if wife_name and wife_name.strip() != "" and wife_name.lower() != 'null':
        msg += format_family_msg("Spouse", wife_name)
        if wife_dob and wife_dob.strip() != "" and wife_dob.lower() != 'null' and wife_dob.strip() != '//':
            msg += format_family_msg("  DOB", wife_dob)
    elif wife_dob and wife_dob.strip() != "" and wife_dob.lower() != 'null' and wife_dob.strip() != '//': # Only DOB for Spouse
        msg += format_family_msg("Spouse DOB", wife_dob)
    
    msg += format_family_msg("Children", str(row[8]) if row[8] else None)
    msg += format_family_msg("Other family members", str(row[9]) if row[9] else None)

    address_parts = [str(row[i]).strip() for i in range(10, 13) if row[i] and str(row[i]).strip() != "" and str(row[i]).lower() != 'null']
    if address_parts:
        msg += "• Add: " + ", ".join([f"**{part}**" for part in address_parts]) + "\n"

    msg += format_family_msg("Mobile", str(row[13]) if row[13] else None, link_type="wa") 
    msg += format_family_msg("Home", str(row[14]) if row[14] else None, link_type="tel")   
    msg += format_family_msg("Family Email", str(row[3]) if row[3] else None) 

    # Spouse Email (row[7]), Husband_Email (row[5])
    spouse_email_val = str(row[7]).strip() if row[7] and str(row[7]).strip().lower() != 'null' else None
    if spouse_email_val:
        display_spouse_email = True
        if len(row) >= 30: # Only compare if full 'code' search result makes row[5] reliable
            husband_email_val = str(row[5]).strip() if row[5] and str(row[5]).strip().lower() != 'null' else None
            if husband_email_val and spouse_email_val == husband_email_val:
                display_spouse_email = False
        
        if display_spouse_email:
            msg += format_family_msg("Spouse Email", spouse_email_val)

    msg += format_family_msg("Home Parish", str(row[15]) if row[15] else None)
    msg += format_family_msg("Membership Date", str(row[16]) if row[16] else None)
    msg += format_family_msg("Related Families", str(row[17]) if row[17] else None)
    msg += format_family_msg("Electoral Roll", str(row[18]) if row[18] is not None else None) # Handle boolean
    msg += format_family_msg("Prayer Group", str(row[19]) if row[19] else None)

    return msg.strip()


# ----------------------------------------------------------------------------------------------------------------------
# This method can be called from a Telegram button or command such as /x V019
def generate_msg_xero_member_payments(name: str, member_code: str, year: str) -> str:
    """
    Generate a message detailing a member's payments for a given year.

    :param name: Name of the member.
    :param member_code: Unique code for the member.
    :param year: Year for which the payments are to be fetched.
    :return: Formatted message string.
    """

    payments = get_member_payments(member_code, year)

    # If no payments are found
    if not payments:
        return f"No contributions for **{name}** for year **{year}**"

    msg = f">**{name}**\n>`For Year {year}`\n"
    msg += "➖➖➖➖➖➖➖\n"

    # If payments list is empty
    if len(payments) == 0:
        msg += "No payments yet"
        return msg

    # Extracting payment details and finding the latest timestamp
    latest_ts = max(item['modified_ts'] for item in payments)

    for item in payments:
        msg += f"► {item['Account']}: **${item['LineAmount']}**\n"

    msg += f"\n`As of: {latest_ts[:16]}`"

    return msg


# ----------------------------------------------------------------------------------------------------------------------
# Return a list of member payments for a year
def get_member_payments(member_code: str, year: str) -> list:
    """
    Fetches member payments for a given member code and year.

    Args:
    - member_code (str): The code of the member.
    - year (str): The year for which payments are to be fetched.

    Returns:
    - list: A list of payment items for the member in the given year.
    """

    contact_id = xero_utils.get_xero_ContactID(member_code)

    if contact_id is None:
        return None

    response = table_member_payments.query(
        KeyConditionExpression=Key('ContactID').eq(contact_id) & Key('AccountCode').begins_with(year)
    )

    return response['Items']


# ----------------------------------------------------------------------------------------------------------------------
# This method can be called from a Telegram button or command such as /xs V019
# Returns a list of all Invoices paid and due for a member
def generate_msg_xero_member_invoices(member_code: str, year: str):
    # Validate the year
    if not is_valid_year(year):
        return f"Not a valid year: **{year}**"

    # Fetch invoices
    invoices = xero_utils.get_Invoices(member_code)

    if not invoices or len(invoices['Invoices']) == 0:
        return f"No invoices for {member_code}"

    # Status to icon mapping
    status_to_icon = {
        "PAID": "🟢",
        "AUTHORISED": "🟠",
        "DRAFT": "🟠"
    }

    msg = f">**Dues**\n\n"
    # msg = f"--**{invoices['Invoices'][0]['Contact']['Name']} ({member_code})**--\n\n"

    for invoice in invoices["Invoices"]:
        # Filter invoices based on conditions
        if (
                invoice["Type"] == "ACCREC"
                and not invoice["InvoiceNumber"].endswith("-VOID")
                and (
                invoice["InvoiceNumber"].startswith(f"INV-{year[2:]}")
                or invoice["InvoiceNumber"].startswith(f"HF-{year[2:]}")
                or (invoice["Status"] == "AUTHORISED" and int(invoice["DateString"].split("-")[0]) <= int(year))
        )
        ):
            # Get icon based on status
            icon = status_to_icon.get(invoice["Status"], "")
            if invoice["Status"] == "AUTHORISED":
                invoice["Status"] = "DUE"

            # Build the message
            invoice_number_display = invoice['InvoiceNumber'] if invoice['InvoiceNumber'] else "-NA-"
            msg += f"**[{invoice_number_display}] - **"

            if invoice["AmountDue"] == 0 or invoice["AmountDue"] == invoice["Total"]:
                msg += f"**${invoice['Total']:,.2f}**: {invoice['Status']} {icon}\n"
            else:
                msg += f"**${invoice['Total']:,.2f}**: ${invoice['AmountDue']:,.2f} {invoice['Status']} {icon}\n"

            for line in invoice["LineItems"]:
                msg += f"  `• {line['Description']}-${line['LineAmount']:,.2f}`\n"

            msg += "––––———————————————\n"

    return msg


# ----------------------------------------------------------------------------------------------------------------------
# Send a message to a Telegram user with an optional inline keyboard
async def edit_and_send_msg(query: CallbackQuery, msg: str, keyboard: InlineKeyboardMarkup = None):
    try:
        await query.message.edit_text(text=msg, reply_markup=keyboard, disable_web_page_preview=True)
    except MessageNotModified as e:
        logger.warning(str(e))
    except BadRequest as e:
        logger.error(str(e))


# ----------------------------------------------------------------------------------------------------------------------
# Return Jan 1 of current year. For Xero accounting methods
def year_start():
    return date(date.today().year, 1, 1).strftime("%Y-%m-%d")


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
def generate_msg_member_auction_contributions(member_code: str) -> Optional[str]:
    """
    Generate a message detailing a member's auction contributions.

    Args:
    - member_code (str): The code identifying the member.

    Returns:
    - str: A formatted message detailing the member's auction contributions or None if there's an error or no contributions.
    """
    try:
        response = table_stosc_harvest_contributors.query(KeyConditionExpression=Key("member_code").eq(member_code))
        items = response.get('Items', [])

        if not items:
            return None

        items_donated = items[0].get('items', [])
        lines = [
            "**Auction Donations**",
            "➖➖➖➖➖➖➖",
            f"Items Donated: {len(items_donated)}",
            "———————"
        ]
        lines.extend(
            f"[`{_item['itemCode']:03}`] **{_item['itemName']}**: {_item['winner']} (${_item['winning_bid']:,}) ({_item['bids']} bids)"
            for _item in items_donated
        )
        lines.append("———————")
        lines.append(f"Total sold for: **${items[0]['total_fetched']:,}**")

        return "\n".join(lines)

    except Exception as e:
        logger.error(e)
        return None


# ----------------------------------------------------------------------------------------------------------------------
def generate_msg_member_auction_purchases(member_code: str) -> str:
    """
    Generate a message for a member's auction purchases.

    Args:
    - member_code (str): The code of the member.

    Returns:
    - str: A formatted message.
    """
    try:
        response = table_stosc_harvest_winners.query(KeyConditionExpression=Key("member_code").eq(member_code))
        items = response.get('Items', [])

        # Check if there are any items in the response
        if not items or not items[0].get('items'):
            return "~ No bids or purchases yet ~\n"

        # Construct the message
        auction_items = items[0]['items']
        msg = [
            "**Auction Wins**",
            "➖➖➖➖➖➖➖",
            f"Items Won: {len(auction_items)}",
            "———————"
        ]

        for item in auction_items:
            item_msg = f"[`{item['itemCode']:03}`] **{item['itemName']}**: ${item['winning_bid']:,} ({item['bids']} bids)"
            msg.append(item_msg)

        msg.append("———————")
        msg.append(f"Total: **${items[0]['total_bid']:,}**")

        return "\n".join(msg)

    except Exception as e:
        logger.error(e)
        return "No Data"


# ----------------------------------------------------------------------------------------------------------------------
async def send_profile_address_and_pic(client: Client, _x: CallbackQuery, msg: str, result: list,
                                       searched_person: str = None, searched_person_name: str = None,
                                       keyboard: InlineKeyboardMarkup = None):
    ZIP_CODE_INDEX = 12
    FAMILY_CODE_INDEX = 0
    PERSON_NAME_INDEX = 1
    ADDRESS_INDEX = 10
    TITLE_INDEX = 2

    # Send if there's a Zip code present and if Family code is searched for
    # Don't map send for person searches

    # Helper function to send photo
    async def send_photo(extension: str):
        if searched_person:
            person_pic_caption = f"{searched_person_name} `({result[0][PERSON_NAME_INDEX]})`"
            # All images are png, so try looking that up first. Adding parameter to the URL to avoid stale cache
            photo_url = f"https://crm.stosc.com/churchcrm/Images/Person/{searched_person}.{extension}?rand={hash(datetime.datetime.today())}"
            logger.info(f"Send Photo URL: {photo_url}")
            await client.send_photo(chat_id=_x.from_user.id, photo=photo_url, caption=person_pic_caption + "\n\n" + msg,
                                    parse_mode=ParseMode.MARKDOWN)
        else:
            photo_url = f"https://crm.stosc.com/churchcrm/Images/Family/{result[0][FAMILY_CODE_INDEX]}.{extension}?rand={hash(datetime.datetime.today())}"
            logger.info(f"Send Photo URL: {photo_url}")
            await client.send_photo(chat_id=_x.from_user.id, photo=photo_url, caption=msg, reply_markup=keyboard,
                                    parse_mode=ParseMode.MARKDOWN)

    # Send venue if conditions are met
    if result[0][ZIP_CODE_INDEX] and not searched_person:
        address_details = get_address_details(result[0][ZIP_CODE_INDEX])
        if address_details:
            lat, lon = address_details
            await client.send_venue(chat_id=_x.from_user.id, latitude=float(lat), longitude=float(lon),
                                    title=result[0][TITLE_INDEX], address=result[0][ADDRESS_INDEX],
                                    disable_notification=True)

    try:
        await send_photo('png')
    except Exception as e1:
        if hasattr(e1, 'ID') and e1.ID == 'MEDIA_EMPTY':
            logger.warning(f"No png image for [{result[0][PERSON_NAME_INDEX]}], trying jpg")
            try:
                await send_photo('jpg')
            except Exception as e2:
                if hasattr(e2, 'ID') and e2.ID == 'MEDIA_EMPTY':
                    logger.warning(f"No png or jpg image for [{result[0][PERSON_NAME_INDEX]}]")
                else:
                    logger.error(f"{getattr(e2, 'MESSAGE', str(e2))}: for [{result[0][PERSON_NAME_INDEX]}]")
                await client.send_message(chat_id=_x.from_user.id, text=msg, reply_markup=keyboard,
                                          disable_web_page_preview=True)
        else:
            logger.error(f"{getattr(e1, 'MESSAGE', str(e1))}: for [{result[0][PERSON_NAME_INDEX]}]")
            await client.send_message(chat_id=_x.from_user.id, text=msg, reply_markup=keyboard,
                                      disable_web_page_preview=True)


# ----------------------------------------------------------------------------------------------------------------------
def is_valid_member_code(member_code: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z]\d{3}', member_code))


# ----------------------------------------------------------------------------------------------------------------------
def is_valid_year(year: str) -> bool:
    """
    Check if a given string is a valid year.

    Args:
        year (str): A string representing the year.

    Returns:
        bool: True if the year is valid, False otherwise.
    """
    if not isinstance(year, str):
        return False
    return len(year) == 4 and re.match(r"^\d{4}$", year) is not None


# ----------------------------------------------------------------------------------------------------------------------
from typing import Union, List, Dict


def get_tracked_projects(raw_data: bool = False) -> Union[str, List[Dict]]:
    response_items = table_stosc_xero_accounts_tracking.scan()['Items']

    # Initialize last_updated to a very old date
    last_updated = '0'
    modified_ts = '0'

    # Using list comprehension to build the message
    tracked_projects = [
        f"• {_item['Name']} - `${_item.get('income', 0.0):,.2f}` | `${_item.get('expense', 0.0):,.2f}`"
        for _item in response_items if _item.get('income') or _item.get('expense')
    ]

    # Update last_updated while iterating
    for _item in response_items:
        modified_ts = _item.get('modified_ts', '0')
        if modified_ts > last_updated:
            last_updated = modified_ts

    if raw_data:
        return response_items

    msg = "**TRACKED PROJECTS**\n" + "➖" * 8 + "\n" + "\n".join(tracked_projects) + f"\n\n`As of: {last_updated}`"
    return msg


# ----------------------------------------------------------------------------------------------------------------------
def get_outstandings():
    """
    Fetch outstanding dues from a pickle file and return as a markdown formatted string.
    """

    # Determine the path based on the environment
    if os.environ.get("ENV") == 'TEST':
        pickle_path = "C:\\DATA\\git\\viper25\\xero_helpers\\outstandings.pickle"
    else:
        pickle_path = os.environ.get("OUTSTANDING_PICKLE_PATH")

    # Use context manager for file handling
    with open(pickle_path, 'rb') as filehandler:
        df = pickle.load(filehandler)

    # Convert dataframe to markdown and format the message
    markdown_data = df.to_markdown()
    msg = f"**OUTSTANDING DUES**\n➖➖➖➖➖➖➖➖\n\n`{markdown_data}`"

    return msg


# ----------------------------------------------------------------------------------------------------------------------

def is_valid_email(email: str) -> bool:
    if not email:
        return False
    # This regex checks for a more standard email format.
    pattern = r"^[a-zA-Z0-9._%+-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


# ----------------------------------------------------------------------------------------------------------------------

def format_telegram_message(msg):
    """Formats the message to comply with Telegram's message length limit."""
    return (msg[:4076] + '\n`... (truncated)`') if len(msg) > 4096 else msg


# ----------------------------------------------------------------------------------------------------------------------
async def get_telegram_file_url(photo):
    path = f"https://api.telegram.org/bot{os.environ.get('STOSC_TELEGRAM_BOT_TOKEN')}/getFile?file_id={photo.file_id}"
    # Do a HTTP get request to the Telegram API to get the file path
    response = requests.get(path)
    response_json = response.json()
    if response_json['ok']:
        file_path = response_json['result']['file_path']
        file_url = f"https://api.telegram.org/file/bot{os.environ.get('STOSC_TELEGRAM_BOT_TOKEN')}/{file_path}"
        logger.debug(f"File URL: {file_url}")
    return file_url


# ----------------------------------------------------------------------------------------------------------------------

def upload_to_s3_and_get_url(image_file, object_name: str):
    s3_resource = boto3.resource(
        "s3",
        aws_access_key_id=os.environ.get("STOSC_DDB_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("STOSC_DDB_SECRET_ACCESS_KEY"),
        region_name="ap-southeast-1",
    )

    object = s3_resource.Object("stoscsg", object_name)
    try:
        s3_response = object.put(Body=open(image_file.name, "rb"), ContentType="image/jpeg")
        logger.debug(f"Uploaded image to S3: {s3_response}")
    except ClientError as e:
        logger.error(f"Error uploading image to S3: {e}")
        return False

    file_path = f"/tmp/{object_name}.jpg"
    file_url = f"https://stoscsg.s3.ap-southeast-1.amazonaws.com/{object_name}"
    logger.info(f"Uploaded file to: {file_url}")
    return file_url


# ----------------------------------------------------------------------------------------------------------------------
def normalize_telephone(param):
    """Normalize the telephone number i.e. remove spaces and hyphens and international codes if any"""
    return re.sub(r"\D", "", param)


# ----------------------------------------------------------------------------------------------------------------------
def valid_telephone(telephone):
    # Validate Singapore telephone numbers
    return re.match(r"^(6|8|9)\d{7}$", telephone)
