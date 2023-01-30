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
table_stosc_xero_accounts_of_interest = resource.Table("stosc_xero_accounts_of_interest")
table_stosc_xero_tokens = resource.Table("stosc_xero_tokens")
# ----------------------------------------------------------------------------------------------------------------------
# get STOSC Member code from Telegram ID
def getMemberCode_from_TelegramID(telegram_id: int):
    response=table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        return response['Items'][0]['member_code']
# ----------------------------------------------------------------------------------------------------------------------
def get_address_details(_zip: str):
    try:
        result=requests.get(f'https://developers.onemap.sg//commonapi/search?searchVal={_zip}&returnGeom=Y&getAddrDetails=Y').json()
        if len(result['results'])>0:
            return result['results'][0]['LATITUDE'], result['results'][0]['LONGITUDE']
    except Exception as e:
        logger.error(f"Exception in onemap API: {e}")
# ----------------------------------------------------------------------------------------------------------------------
# Generate a Member Profile msg
def generate_profile_msg_for_family(result: list):
    msg = f"• Family: **{result[0][2]} ({result[0][1]})**\n"
    msg += f"• DOB: **{result[0][20]}**\n" if (result[0][20] != "" and result[0][20] is not None) else ""
    msg += f"• Spouse: **{result[0][6]}**\n" if (result[0][6] != "" and result[0][6] is not None) else ""
    msg += f"• Spouse DOB: **{result[0][21]}**\n" if (result[0][21] != "" and result[0][21] is not None) else ""
    msg += f"• Children: **{result[0][8]}**\n" if (result[0][8] != "" and result[0][8] is not None) else ""
    msg += f"• Other family members: **{result[0][9]}**\n" if (result[0][9] != "" and result[0][9] is not None) else ""
    if (result[0][10] != "" and result[0][10] is not None):
        msg += f"• Add: **{result[0][10]}**"
    if (result[0][11] != "" and result[0][11] is not None):
        msg += f"**, {result[0][11]}**"
    if (result[0][12] != "" and result[0][12] is not None):
        msg += f", **{result[0][12]}**"
    msg += "\n"
    msg += f"• Mobile: [{result[0][13]}](tel://{result[0][13]})\n" if (result[0][13] != "" and result[0][13] is not None) else ""
    msg += f"• Home: [{result[0][14]}](tel://{result[0][14]})\n" if (result[0][14] != "" and result[0][14] is not None) else ""
    msg += f"• Email: **{result[0][3]}**\n" if (result[0][3] != "" and result[0][3] is not None) else ""
    msg += f"• Spouse Email: **{result[0][7]}**\n" if (result[0][7] != "" and result[0][7] is not None and result[0][7]!=result[0][5]) else ""
    msg += f"• Home Parish: **{result[0][15]}**\n" if (result[0][15] != "" and result[0][15] is not None) else ""
    msg += f"• Membership Date: **{result[0][16]}**\n" if (result[0][16] != "" and result[0][16] is not None) else ""
    msg += f"• Related Families: **{result[0][17]}**\n" if (result[0][17] != "" and result[0][17] is not None) else ""
    msg += f"• Electoral Roll: **{result[0][18]}**\n" if (result[0][18] != "" and result[0][18] is not None) else ""
    msg += f"• Prayer Group: **{result[0][19]}**\n" if (result[0][19] != "" and result[0][19] is not None) else ""
    return msg

# ----------------------------------------------------------------------------------------------------------------------
# This method can be called from a Telegram button or command such as /x V019
def generate_msg_xero_member_payments(name: str, _member_code: str, _year: str):
    payments = get_member_payments(_member_code, _year)
    if payments:
        msg=f"**{name}**\n`For Year {_year}`\n"
        msg += "➖➖➖➖➖➖➖\n"
        if len(payments) == 0:
            msg += "No payments yet"
        latest_ts=''
        for item in payments:
            msg += f"► {item['Account']}: **${str(item['LineAmount'])}**\n"
            latest_ts=item['modfied_ts'] if (item['modfied_ts'] > latest_ts) else latest_ts
        if latest_ts != '':
            msg += f"\n`As of: {latest_ts[:16]}`"
        return msg
    return f"No contributions for **{name}** for year **{_year}**"
# ----------------------------------------------------------------------------------------------------------------------
# Return a list of member payments for a year
def get_member_payments(_member_code: str, _year: str) -> list:
    xero_contactID = xero_utils.get_xero_ContactID(_member_code)
    if xero_contactID is not None:
        response=table_member_payments.query(KeyConditionExpression=Key('ContactID').eq(xero_contactID) & Key('AccountCode').begins_with(_year))
    else:
        return None
    return response['Items']

# ----------------------------------------------------------------------------------------------------------------------
# This method can be called from a Telegram button or command such as /xs V019
# Returns a list of all Invoices paid and due for a member
def generate_msg_xero_member_invoices(_member_code: str, _year: str):
    if not is_valid_year(_year):
       return f"Not a valid year: **{_year}**"
    _invoices=xero_utils.get_Invoices(_member_code)
    if _invoices and len(_invoices['Invoices'])> 0:
        msg=f"--**{_invoices['Invoices'][0]['Contact']['Name']} ({_member_code})**--\n\n"
        icon='🟠' 
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
                if invoice['AmountDue'] > 0:
                    msg += f"**[(PayNow link)](https://stosc.com/paynow/?invoiceNo={invoice['InvoiceNumber']}&amp;currency=SGD&amount={invoice['AmountDue']}&shortCode=!wL!x0)**\n"
                msg += "––––————————————————\n"
        return msg
    return f"No invoices for {_member_code}"

# ----------------------------------------------------------------------------------------------------------------------
# Send a message to a Telegram user with an optional inline keyboard
async def edit_and_send_msg(query: CallbackQuery, msg: str, keyboard: InlineKeyboardMarkup=None):
    try:
        await query.message.edit_text(text=msg,reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        if e.ID == 'MESSAGE_NOT_MODIFIED':  
            logger.warn(e.MESSAGE)
        else:
            logger.error(e.MESSAGE)
# ----------------------------------------------------------------------------------------------------------------------
# Return Jan 1 of current year. For Xero accounting methods
def year_start():
    return date(date.today().year, 1, 1).strftime("%Y-%m-%d")\
# ----------------------------------------------------------------------------------------------------------------------
# Return the start of the week (from Sunday 7.45 AM onwards)
def week_start_from_service_time():
    # Set to Sunday at current time
    start_of_week = datetime.datetime.today() - timedelta(days=datetime.datetime.today().weekday()+1) 
    # Set to 7.45 AM (because we start accepting new prayers at 7.45 AM)
    return start_of_week.replace(hour=7, minute=45)
# ----------------------------------------------------------------------------------------------------------------------
# # Return current date
def todays_date():
    return date.today().strftime("%Y-%m-%d")
#----------------------------------------------------------------------------------------------------------------------
# Return date a week ago
def a_week_ago():
    return datetime.datetime.today() - timedelta(days=7)
# ----------------------------------------------------------------------------------------------------------------------
def get_member_auction_link(_member_code: str):
    response = table_harvest_members.query(KeyConditionExpression=Key("code").eq(_member_code))
    if len(response['Items']) > 0:
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
            if len(response['Items'][0]['items'])>0:
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
async def send_profile_address_and_pic(client: Client, _x: CallbackQuery, msg: str, result: list, searched_person: str=None, searched_person_name:str=None, keyboard: InlineKeyboardMarkup = None):
    # Send if there's a Zip code present and if Family code is searched for
    # Don't map send for person searches
    if (result[0][12] != "" and result[0][12] is not None and searched_person is None): 
        if get_address_details(result[0][12]):
            lat, lon=get_address_details(result[0][12])
            await client.send_venue(chat_id=_x.from_user.id,latitude=float(lat),longitude=float(lon),title=result[0][2],address=result[0][10],disable_notification=True)
    try:
        # All images are png, so try looking that up first. Adding parameter to the URL to avoid stale cache 
        if searched_person:
            person_pic_caption = f"{searched_person_name} `({result[0][1]})`"
            await client.send_photo(chat_id=_x.from_user.id,photo=f"https://crm.stosc.com/churchcrm/Images/Person/{searched_person}.png?rand={hash(datetime.datetime.today())}", caption=person_pic_caption + "\n\n" + msg)
        # Send family pic only for searches by member code
        if searched_person is None:
            await client.send_photo(chat_id=_x.from_user.id,photo=f"https://crm.stosc.com/churchcrm/Images/Family/{result[0][0]}.png?rand={hash(datetime.datetime.today())}", caption=msg, reply_markup=keyboard)
    except Exception as e1:
        if e1.ID == 'MEDIA_EMPTY':
            logger.warn(f"No png image for [{result[0][1]}], trying jpg")
        else:
            logger.error(f"{e1.MESSAGE}: for [{result[0][1]}]")
        try:
            # If no png, try looking for a jpg
            if searched_person:
                person_pic_caption = f"{searched_person_name} `({result[0][1]})`"
                await client.send_photo(chat_id=_x.from_user.id,photo=f"https://crm.stosc.com/churchcrm/Images/Person/{searched_person}.jpg?rand={hash(datetime.datetime.today())}", caption=person_pic_caption)
            await client.send_photo(chat_id=_x.from_user.id,photo=f"https://crm.stosc.com/churchcrm/Images/Family/{result[0][0]}.jpg?rand={hash(datetime.datetime.today())}", caption=msg, reply_markup=keyboard)    
        except Exception as e2:
            if e2.ID == 'MEDIA_EMPTY':               
                logger.warn(f"No png or jpg image for [{result[0][1]}]")
                # No Image found, send details without photo then
                await client.send_message(chat_id=_x.from_user.id,text=msg, reply_markup=keyboard)
            else:
                logger.error(f"{e2.MESSAGE}: for [{result[0][1]}]")
                await client.send_message(chat_id=_x.from_user.id,text=msg, reply_markup=keyboard)
# ----------------------------------------------------------------------------------------------------------------------
def is_valid_member_code(_member_code: str):
    if not _member_code:
        return False
    if len(_member_code) != 4:
        return False
    if not re.match('[A-Za-z]\d{3}', _member_code):
        return False
    return True
# ----------------------------------------------------------------------------------------------------------------------
def is_valid_year(year: str):
    return len(year) == 4 and (re.match('\d{4}', year) is not None)
# ----------------------------------------------------------------------------------------------------------------------
def get_tracked_projects(raw_data: bool=False):
    response = table_stosc_xero_accounts_of_interest.scan()
    if raw_data:
        return response["Items"]
    msg = "**TRACKED PROJECTS**\n"
    msg += "➖➖➖➖➖➖➖➖\n\n"
    for _item in response["Items"]:
        if _item['Total']:
            msg += f"• {_item['AccountName']} - `${_item['Total']:,.2f}`\n"
    return msg
# ----------------------------------------------------------------------------------------------------------------------
def get_outstandings():
    msg = "**OUTSTANDING DUES**\n"
    msg += "➖➖➖➖➖➖➖➖\n\n"
    if os.environ.get("ENV")=='TEST':
        filehandler = open("C:\\DATA\\git\\viper25\\xero_helpers\\outstandings.pickle",'rb')
    else:
        filehandler = open(os.environ.get("OUTSTANDING_PICKLE_PATH"),'rb')
    df = pickle.load(filehandler)
    msg = df.to_markdown()
    msg = f"`{msg}`"
    return msg

# ----------------------------------------------------------------------------------------------------------------------
def is_valid_email(email:str):
    if not email:
        return False
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    return True