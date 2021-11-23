import os
import boto3
from boto3.dynamodb.conditions import Key
from stoscbots.db import db
from stoscbots.xero import xero_utils
from stoscbots.util import loggers
from datetime import date
import datetime
from datetime import timedelta
import requests

resource = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ.get("STOSC_DDB_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("STOSC_DDB_SECRET_ACCESS_KEY"),
    region_name="ap-southeast-1",
)
table_stosc_bot_member_telegram=resource.Table('stosc_bot_member_telegram')
table_member_payments=resource.Table('member_payments')
table_members=resource.Table('member_payments')
table_harvest_metrics=resource.Table('stosc_harvest_metrics')
table_harvest_items = resource.Table("stosc_harvest_items")
table_harvest_members = resource.Table("stosc_harvest_members")

# ----------------------------------------------------------------------------------------------------------------------
# get STOSC Member code from Telegram ID
def getMemberCode_from_TelegramID(telegram_id):
    response=table_stosc_bot_member_telegram.query(KeyConditionExpression=Key('telegram_id').eq(str(telegram_id)))
    if len(response['Items']) == 1:
        return response['Items'][0]['member_code']
    else:
        return None
# ----------------------------------------------------------------------------------------------------------------------
def get_address_details(_zip):
    try:
        result=requests.get(f'https://developers.onemap.sg//commonapi/search?searchVal={_zip}&returnGeom=Y&getAddrDetails=Y').json()
        if len(result['results'])>0:
            return result['results'][0]['LATITUDE'], result['results'][0]['LONGITUDE']
        else:
            return None, None
    except Exception as e:
        loggers.error(f"Exception in onemap API: {e}")
        return None, None
# ----------------------------------------------------------------------------------------------------------------------
# Generate a Member Profile msg
def generate_profile_msg(result):
    msg=f"• Name: **{result[0][1]}**\n"
    if (result[0][2] != "" and result[0][2] is not None):
        msg += f"• Add: **{result[0][2]}**"
    if (result[0][3] != "" and result[0][3] is not None):
        msg += f"**, {result[0][3]}**"
    if (result[0][4] != "" and result[0][4] is not None):
        msg += f", **{result[0][4]}**"
    msg += "\n"
    msg += f"• Mobile: [{result[0][5]}](tel://{result[0][5]})\n" if (result[0][5] != "" and result[0][5] is not None) else ""
    msg += f"• Home: [{result[0][6]}](tel://{result[0][6]})\n" if (result[0][6] != "" and result[0][6] is not None) else ""
    msg += f"• Email: **{result[0][7]}**\n" if (result[0][7] != "" and result[0][7] is not None) else ""
    msg += f"• Home Parish: **{result[0][8]}**\n" if (result[0][8] != "" and result[0][8] is not None) else ""
    msg += f"• Membership Date: **{result[0][9]}**\n" if (result[0][9] != "" and result[0][9] is not None) else ""
    msg += f"• Related Families: **{result[0][10]}**\n" if (result[0][10] != "" and result[0][10] is not None) else ""
    msg += f"• Electoral Roll: **{result[0][11]}**\n" if (result[0][11] != "" and result[0][11] is not None) else ""
    msg += f"• Prayer Group: **{result[0][12]}**\n" if (result[0][12] != "" and result[0][12] is not None) else ""
    return msg

# ----------------------------------------------------------------------------------------------------------------------
# This method can be called from a Telegram button or command such as /x V019
def generate_msg_xero_member_payments(_member_code, _year):
    result=db.get_member_details(_member_code,'code')
    _contactID=xero_utils.get_xero_ContactID(_member_code)
    if _contactID is not None:
        response=table_member_payments.query(KeyConditionExpression=Key('ContactID').eq(_contactID) & Key('AccountCode').begins_with(_year))
        msg=f"**{result[0][1]}**\n`For Year {_year}`\n"
        msg += "➖➖➖➖➖➖➖\n"
        if len(response['Items']) == 0:
            msg += "No payments yet"
        latest_ts=''
        for item in response['Items']:
            msg += f"► {item['Account']}: **${str(item['LineAmount'])}**\n"
            latest_ts=item['modfied_ts'] if (item['modfied_ts'] > latest_ts) else latest_ts
        if latest_ts != '':
            msg += f"\n`As of: {latest_ts[:16]}`"
        return msg
    else:
        return f"No contactID for {_member_code}"
# ----------------------------------------------------------------------------------------------------------------------
# This method can be called from a Telegram button or command such as /xs V019
# Returns a list of all Invoices paid and due for a member
def generate_msg_xero_member_invoices(_member_code, _year):
    _invoices=xero_utils.get_Invoices(_member_code)
    if _invoices and len(_invoices['Invoices'])> 0:
        msg=f"--**{_invoices['Invoices'][0]['Contact']['Name']} ({_member_code})**--\n\n"
        icon='🟠' 
        for invoice in _invoices['Invoices']:
            if invoice['InvoiceNumber'].endswith('-VOID'):
                # Skip invoices that were VOIDED manually in FY21. These have a -VOID at the end
                continue
            loggers.debug(f"Invoice No: {invoice['InvoiceNumber']} for amount: {invoice['AmountDue']}")
            if invoice['Status'] == 'PAID':
                icon='🟢'
            elif invoice['Status'] == 'AUTHORISED':
                icon='🟠'
            elif invoice['Status'] == 'VOIDED':
                icon='🔴'
            elif invoice['Status'] == 'DRAFT':
                icon='🟠'
            elif invoice['Status'] == 'DELETED':
                # Don't show DELETED invoices
                continue
            msg += f"**[{invoice['InvoiceNumber']}] - **" if (invoice['InvoiceNumber'] != '' and invoice['InvoiceNumber'] is not None) else '[`-NA-`] - '
            msg += f"{invoice['Status']} {icon}\n"
            for line in invoice['LineItems']:
                            #msg += "−−−−\n"
                msg += f"  `{line['Description']}-${line['LineAmount']:,.2f}`\n"
            msg += "––––————————————————\n"
        return msg
    else:
        return f"No invoices for {_member_code}"

# ----------------------------------------------------------------------------------------------------------------------
# Send a message to a Telegram user with an optional inline keyboard
def edit_and_send_msg(query, msg, keyboard=None):
    try:
        query.message.edit_text(text=msg,reply_markup=keyboard)
    except Exception as e:
        if e.ID == 'MESSAGE_NOT_MODIFIED':  
            loggers.warn(e.MESSAGE)
        else:
            loggers.error(e.MESSAGE)
# ----------------------------------------------------------------------------------------------------------------------
# Return Jan 1 of current year. For Xero accounting methods
def year_start():
    return date(date.today().year, 1, 1).strftime("%Y-%m-%d")\
# ----------------------------------------------------------------------------------------------------------------------
# Return current date
def todays_date():
    return date.today().strftime("%Y-%m-%d")
#-----------------------------------------------------------------------------------    
# Return date a week ago
def a_week_ago():
    return datetime.datetime.today() - timedelta(days=7)
# ----------------------------------------------------------------------------------------------------------------------
def get_member_auction_link(_member_code):
    response = table_harvest_members.query(KeyConditionExpression=Key("code").eq(_member_code))
    _link = f"https://harvest.stosc.com/?id={response['Items'][0]['guid']}"
    return _link
# ----------------------------------------------------------------------------------------------------------------------
# Get Winning Bid for an Item
def __get_winning_bid(_itemCode):
    response = table_harvest_items.query(KeyConditionExpression=Key("itemCode").eq(int(_itemCode)))
    if "winning_bid" in response["Items"][0].keys():
        return response["Items"][0]["winning_bid"]
    else:
        return None
# ----------------------------------------------------------------------------------------------------------------------
def generate_msg_member_auction_purchases(_member_code):
    response = table_harvest_metrics.query(KeyConditionExpression=Key("pk").eq("user") & Key("sk").begins_with(_member_code))
    if len(response["Items"]) != 0:
        msg = f"**{response['Items'][0]['sk'][5:]}**\n"
        msg += "➖➖➖➖➖➖➖\n"
        if "amt" in response["Items"][0].keys():
            msg += f"Total: **${response['Items'][0]['amt']:,}**\n"
        msg += f"Bids Placed: {response['Items'][0]['bidCount']}\n"
        if "items_won" in response["Items"][0].keys():
            msg += f"Items Won: {len(response['Items'][0]['items_won'])}\n"
            msg += "———————\n"
            for _item in response["Items"][0]["items_won"]:
                # Get the winning price for that item
                msg += f"[`{_item.split('-')[0]}`] {_item.split('-')[1]}: **${__get_winning_bid(_item.split('-')[0]):,}**\n"
    else:
        msg = "No Purchases yet\n"
    return msg
# ----------------------------------------------------------------------------------------------------------------------
def send_profile_address_and_pic(client, _x, msg,result, keyboard = None):
    if (result[0][4] != "" and result[0][4] is not None): 
        lat, lon=get_address_details(result[0][4])
        client.send_venue(chat_id=_x.from_user.id,latitude=float(lat),longitude=float(lon),title=result[0][1],address=result[0][2],disable_notification=True)
    try:
        # Per Simon, all images are png, so try looking that up first   
        client.send_photo(chat_id=_x.from_user.id,photo=f"https://crm.stosc.com/churchcrm/Images/Family/{result[0][0]}.png", caption=msg, reply_markup=keyboard)
    except Exception as e1:
        if e1.ID == 'MEDIA_EMPTY':
            loggers.warn(f"No png image for [{result[0][1]}], trying png")
        else:
            loggers.error(f"{e1.MESSAGE}: for [{result[0][1]}]")
        try:
            # If no png, try looking for a jpg
            client.send_photo(chat_id=_x.from_user.id,photo=f"https://crm.stosc.com/churchcrm/Images/Family/{result[0][0]}.jpg", caption=msg, reply_markup=keyboard)    
        except Exception as e2:
            if e2.ID == 'MEDIA_EMPTY':               
                loggers.warn(f"No jpg image for [{result[0][1]}]")
                # No Image found, send details without photo then
                client.send_message(chat_id=_x.from_user.id,text=msg, reply_markup=keyboard)
            else:
                loggers.error(f"{e2.MESSAGE}: for [{result[0][1]}]")
# ----------------------------------------------------------------------------------------------------------------------


        