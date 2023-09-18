import logging
import os
from datetime import datetime

import boto3
import requests
from boto3.dynamodb.conditions import Key

from stoscbots.util import utils
from stoscbots.util.loggers import LOGLEVEL

# ----------------------------------------------------------------------------------------------------------------------
# Constants and Global Variables
# ----------------------------------------------------------------------------------------------------------------------

LOGGER = logging.getLogger('Xero.Utils')
LOGGER.setLevel(LOGLEVEL)

XERO_TENANT_ID = os.environ.get('STOSC_XERO_STOSC_TENANT_ID')
XERO_CLIENT_ID = os.environ.get('STOSC_XERO_CLIENT_ID')
STOSC_REFRESH_TOKEN_KEY = "stosc-bot"

RESOURCE = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ.get("STOSC_DDB_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("STOSC_DDB_SECRET_ACCESS_KEY"),
    region_name="ap-southeast-1",
)
TABLE = RESOURCE.Table('stosc_xero_tokens')
XERO_API_BASE_URL = 'https://api.xero.com/api.xro/2.0'


# ----------------------------------------------------------------------------------------------------------------------
# Token Management
# Access tokens (or Bearer tokens) are valid for 30 mins and
# Refresh tokens for 60 days
# ----------------------------------------------------------------------------------------------------------------------


def _get_refresh_token():
    response = TABLE.query(KeyConditionExpression=Key('token').eq(STOSC_REFRESH_TOKEN_KEY))
    return response['Items'][0]['refresh_token']


def _update_refresh_token(current_refresh_token):
    chunk = {
        "token": STOSC_REFRESH_TOKEN_KEY,
        "refresh_token": current_refresh_token,
        "modified_ts": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }
    TABLE.put_item(Item=chunk)


def _get_access_token():
    old_refresh_token = _get_refresh_token()
    url = 'https://identity.xero.com/connect/token'
    response = requests.post(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={
        'grant_type': 'refresh_token',
        'client_id': XERO_CLIENT_ID,
        'refresh_token': old_refresh_token,
    })
    response_data = response.json()
    _update_refresh_token(response_data['refresh_token'])
    return response_data['access_token']


_access_token = None


def get_access_token():
    global _access_token
    if _access_token is None:
        _access_token = _get_access_token()
    return _access_token


# ----------------------------------------------------------------------------------------------------------------------
# HTTP Request Management
# ----------------------------------------------------------------------------------------------------------------------

# Make the GET HTTP call to XERO API
def __xero_get(url: str, **extra_headers):
    # Setting as global since it can be modified by this function if access token has expired
    global _access_token

    def get_headers():
        return {
            'Authorization': 'Bearer ' + get_access_token(),
            'Accept': 'application/json',
            'Xero-tenant-id': XERO_TENANT_ID,
            **extra_headers,
        }

    response = requests.get(url, headers=get_headers())
    if response.status_code == 401:
        # Access token has expired. Get a new one and set globally
        LOGGER.info("Access Token has expired. Getting a new one.")
        _access_token = _get_access_token()
        # Make the call again with new access token
        response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        return response.json()
    else:
        LOGGER.error(f"Failed to fetch data from Xero API. Status code: {response.status_code}")
        return None


def construct_url(endpoint, **params):
    url = f"{XERO_API_BASE_URL}/{endpoint}"
    if params:
        query_params = "&".join(f"{key}={value}" for key, value in params.items())
        url = f"{url}?{query_params}"
    return url


# ----------------------------------------------------------------------------------------------------------------------
def get_xero_ContactID(code: str = None):
    LOGGER.debug(f"Getting ContactID for {code}")
    endpoint = f'Contacts?where=AccountNumber=="{code}"'
    url = construct_url(endpoint)
    contacts = __xero_get(url)
    if len(contacts['Contacts']) > 0:
        return contacts['Contacts'][0]['ContactID']


# ----------------------------------------------------------------------------------------------------------------------
# Retrieve all AUTHORISED and PAID Invoices for a ContactID
def get_Invoices(memberID: str):
    LOGGER.debug(f"Getting Invoices for {memberID}")
    _contactID = get_xero_ContactID(memberID)
    if _contactID:
        endpoint = f"Invoices?ContactIDs={_contactID}&Statuses=AUTHORISED,PAID"
        url = construct_url(endpoint)
        # Add If-Modified-Since HTTP header to get this year's invoices only
        # _header={'If-Modified-Since': utils.year_start()}
        # return __xero_get(url,**_header)
        return __xero_get(url)


# ----------------------------------------------------------------------------------------------------------------------
def get_executive_summary():
    LOGGER.debug(f"Getting Executive Summary")
    url = construct_url('Reports/ExecutiveSummary')
    return __xero_get(url)


# ----------------------------------------------------------------------------------------------------------------------
# Returns the balances and cash movements for each bank account
def get_bank_summary():
    LOGGER.debug(f"Getting Bank Summary")
    url = construct_url('Reports/BankSummary', fromDatedate=utils.year_start(), toDate=utils.todays_date())
    return __xero_get(url)


# ----------------------------------------------------------------------------------------------------------------------
# Returns a trial balance for the current month up to the date specified. YTD values are shown too.
# Set paymentsOnly=true to get Cash Basis (actual payments and not receivables)
def xero_get_trial_balance(_paymentsOnly: bool = False):
    LOGGER.debug(f"Getting Trial Balance")
    url = construct_url('Reports/TrialBalance', paymentsOnly=_paymentsOnly, date=utils.todays_date())
    return __xero_get(url)


# ----------------------------------------------------------------------------------------------------------------------
def xero_get_payments():
    LOGGER.debug(f"xero_get_payments: Getting Payments")
    _week_ago = utils.a_week_ago()
    url = construct_url('Payments',
                        where=f"Date>DateTime({_week_ago.year}, {_week_ago.month}, {_week_ago.day})",
                        order='Date')
    return __xero_get(url)


# -----------------------------------------------------------------------------------
def xero_get_bank_transactions():
    LOGGER.debug(f"Getting Bank Transactions")
    _week_ago = utils.a_week_ago()
    url = construct_url('BankTransactions',
                        where=f"Date>DateTime({_week_ago.year}, {_week_ago.month}, {_week_ago.day})",
                        order='Date')
    return __xero_get(url)


# -----------------------------------------------------------------------------------
# Xero dates are weird. Parse
def parse_Xero_Date(_date: str):
    LOGGER.debug(f"parse_Xero_Date: Parsing Xero date: {_date}")
    return datetime.fromtimestamp(int(_date[6:-2].split('+')[0]) / 1000)


# -----------------------------------------------------------------------------------
def get_chart_of_accounts(class_type: str = None) -> list[dict]:
    LOGGER.info(f"Initializing Chart of Accounts")
    # https://api.xero.com/api.xro/2.0/Accounts?where=Status="ACTIVE"&&Class="REVENUE"
    # doesn't seem to filter at server side.
    url = construct_url('Accounts')
    accounts = __xero_get(url)['Accounts']
    accounts = [x for x in accounts if x['Status'] == 'ACTIVE']
    if class_type:
        accounts = [x for x in accounts if x['Class'] == class_type]
    return accounts
