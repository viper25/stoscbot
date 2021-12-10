import os
import requests
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from stoscbots.util import utils

XERO_TENANT_ID=os.environ.get('STOSC_XERO_STOSC_TENANT_ID')
XERO_CLIENT_ID=os.environ.get('STOSC_XERO_CLIENT_ID')
REFRESH_TOKEN_KEY="stosc-bot"

resource = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ.get("STOSC_DDB_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("STOSC_DDB_SECRET_ACCESS_KEY"),
    region_name="ap-southeast-1",
)
table=resource.Table('stosc_xero_tokens')

# Refresh access_token. Use the refresh_token to keep the access_token "fresh" every 30 mins. 
def __xero_get_Access_Token():
    # Get current refresh token
    response=table.query(KeyConditionExpression=Key('token').eq(REFRESH_TOKEN_KEY))
    old_refresh_token=response['Items'][0]['refresh_token']
    
    url = 'https://identity.xero.com/connect/token'
    response=requests.post(url,headers={
        'Content-Type' : 'application/x-www-form-urlencoded'},data={
            'grant_type': 'refresh_token',
            'client_id' : XERO_CLIENT_ID,
            'refresh_token': old_refresh_token
            })
    response_dict=response.json()
    current_refresh_token=response_dict['refresh_token']

    # Set new refresh token
    chunk={"token":REFRESH_TOKEN_KEY, 'refresh_token':current_refresh_token, 'modfied_ts': datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    table.put_item(Item=chunk)

    return response_dict['access_token']

# Make the GET HTTP call to XERO API
def __xero_get(url, **extra_headers):
    _headers={
        'Authorization': 'Bearer ' + __xero_get_Access_Token(),
        'Accept': 'application/json',
        'Xero-tenant-id': XERO_TENANT_ID
    }
    # Some API calls require adding the modified date to get just this year's transaction and 
    # not from the very begining
    if extra_headers: 
        _headers.update(extra_headers)
    response=requests.get(url,headers=_headers)
    return response.json()

# ----------------------------------------------------------------------------------------------------------------------    
def get_xero_ContactID(code=None):
    url = f'https://api.xero.com/api.xro/2.0/Contacts?where=AccountNumber=="{code}"'
    contacts=__xero_get(url)
    if len(contacts['Contacts'])>0:
        return contacts['Contacts'][0]['ContactID']
# ----------------------------------------------------------------------------------------------------------------------
# Retrieve all AUTHORISED and PAID Invoices for a ContactID
def get_Invoices(memberID):
    _contactID=get_xero_ContactID(memberID)
    if _contactID:
        url = f"https://api.xero.com/api.xro/2.0/Invoices?ContactIDs={_contactID}"
        # Add If-Modified-Since HTTP header to get this year's invoices only
        _header={'If-Modified-Since': utils.year_start()}
        return __xero_get(url,**_header)

# ----------------------------------------------------------------------------------------------------------------------
def get_executive_summary():
    url = 'https://api.xero.com/api.xro/2.0/Reports/ExecutiveSummary'
    return __xero_get(url)
# ----------------------------------------------------------------------------------------------------------------------
# Returns the balances and cash movements for each bank account
def get_bank_summary():
    url = f'https://api.xero.com/api.xro/2.0/Reports/BankSummary?fromDatedate={utils.year_start()}&toDate={utils.todays_date()}'
    return __xero_get(url)
# ----------------------------------------------------------------------------------------------------------------------
# Returns a trial balance for the current month up to the date specified. YTD values are shown too.
def xero_get_trial_balance():
    url = f'https://api.xero.com/api.xro/2.0/Reports/TrialBalance?date={utils.todays_date()}'
    return __xero_get(url)
# ----------------------------------------------------------------------------------------------------------------------
def xero_get_payments():
    _week_ago=utils.a_week_ago()
    url = f"https://api.xero.com/api.xro/2.0/Payments?where=Date>DateTime({_week_ago.year}, {_week_ago.month}, {_week_ago.day})&order=Date"
    return __xero_get(url)
#-----------------------------------------------------------------------------------    
def xero_get_bank_transactions():
    _week_ago=utils.a_week_ago()
    url = f"https://api.xero.com/api.xro/2.0/BankTransactions?where=Date>DateTime({_week_ago.year}, {_week_ago.month}, {_week_ago.day})&order=Date"
    return __xero_get(url)    
#-----------------------------------------------------------------------------------    
# Xero dates are weird. Parse
def parse_Xero_Date(_date):
    return datetime.fromtimestamp(int(_date[6:-2].split('+')[0])/1000)    