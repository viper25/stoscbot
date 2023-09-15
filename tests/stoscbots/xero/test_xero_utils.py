from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from stoscbots.xero.xero_utils import _get_refresh_token, _update_refresh_token, _get_access_token, __xero_get, \
    construct_url, get_xero_ContactID, get_Invoices, get_executive_summary, get_bank_summary, xero_get_trial_balance, \
    xero_get_payments, xero_get_bank_transactions, parse_Xero_Date

MODULE_NAME = "stoscbots.xero.xero_utils"


@pytest.fixture
def dynamodb_table_mock():
    with patch(f'{MODULE_NAME}.TABLE') as mock:
        mock.put_item = MagicMock()
        yield mock


@pytest.fixture
def requests_post_mock():
    with patch(f'{MODULE_NAME}.requests.post') as mock:
        yield mock


@pytest.fixture
def session_get_mock():
    with patch(f'{MODULE_NAME}.session.get') as mock:
        yield mock


@pytest.fixture
def get_access_token_mock():
    '''
    This ensures that a mocked token is used during the test, and _get_access_token
    (which updates the DynamoDB) is not called. It also assures that _access_token remains None
    during the test, preventing any unintentional side effects.
    '''
    with patch(f'{MODULE_NAME}.get_access_token') as mock:
        mock.return_value = 'mock_access_token'
        yield mock

@pytest.fixture
def get_xero_ContactID_mock():
    with patch(f'{MODULE_NAME}.get_xero_ContactID') as mock:
        yield mock

@pytest.fixture
def construct_url_mock():
    with patch(f'{MODULE_NAME}.construct_url') as mock:
        yield mock

@pytest.fixture
def xero_get_mock():
    with patch(f'{MODULE_NAME}.__xero_get') as mock:
        yield mock


# ----------------------------------------------------------------------------------------------------------------------

def test_get_refresh_token(dynamodb_table_mock):
    dynamodb_table_mock.query.return_value = {'Items': [{'refresh_token': 'sample_refresh_token'}]}
    result = _get_refresh_token()
    assert result == 'sample_refresh_token'


def test_update_refresh_token(dynamodb_table_mock):
    _update_refresh_token('new_refresh_token')
    dynamodb_table_mock.put_item.assert_called_once()


def test_get_access_token(dynamodb_table_mock, requests_post_mock):
    dynamodb_table_mock.query.return_value = {'Items': [{'refresh_token': 'sample_refresh_token'}]}
    requests_post_mock.return_value.json.return_value = {'refresh_token': 'new_refresh_token',
                                                         'access_token': 'new_access_token'}
    result = _get_access_token()
    assert result == 'new_access_token'


def test_xero_get(session_get_mock, get_access_token_mock):
    session_get_mock.return_value.status_code = 200
    session_get_mock.return_value.json.return_value = {'data': 'response_data'}
    result = __xero_get('sample_url')
    assert result == {'data': 'response_data'}


def test_construct_url():
    result = construct_url('endpoint', param1='value1', param2='value2')
    assert result == 'https://api.xero.com/api.xro/2.0/endpoint?param1=value1&param2=value2'


def test_get_xero_ContactID(session_get_mock, get_access_token_mock):
    session_get_mock.return_value.status_code = 200
    session_get_mock.return_value.json.return_value = {'Contacts': [{'ContactID': 'sample_contact_id'}]}
    result = get_xero_ContactID('sample_code')
    assert result == 'sample_contact_id'

def test_get_Invoices(get_xero_ContactID_mock, xero_get_mock):
    get_xero_ContactID_mock.return_value = 'mock_contact_id'
    xero_get_mock.return_value = {'some_key': 'some_value'}

    result = get_Invoices('test_memberID')
    assert result == {'some_key': 'some_value'}


def test_get_executive_summary(xero_get_mock):
    xero_get_mock.return_value = {'some_key': 'some_value'}
    result = get_executive_summary()
    assert result == {'some_key': 'some_value'}

def test_parse_Xero_Date():
    input_date = "/Date(1672466400000+0000)/"
    expected_output = datetime.fromtimestamp(1672466400)
    result = parse_Xero_Date(input_date)
    assert result == expected_output

