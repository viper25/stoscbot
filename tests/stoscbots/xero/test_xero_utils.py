from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from stoscbots.xero.xero_utils import _get_refresh_token, _update_refresh_token, _get_access_token, construct_url, \
    get_xero_ContactID, get_Invoices, get_executive_summary, parse_Xero_Date

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


def test_construct_url():
    result = construct_url('endpoint', param1='value1', param2='value2')
    assert result == 'https://api.xero.com/api.xro/2.0/endpoint?param1=value1&param2=value2'


def test_get_xero_ContactID_success():
    code = "12345"
    mock_contactID = "contact_12345"
    mock_response = {
        "Contacts": [
            {"ContactID": mock_contactID}
        ]
    }
    with patch(f'{MODULE_NAME}.__xero_get', return_value=mock_response), \
            patch(f'{MODULE_NAME}.construct_url',
                  return_value="http://api.xero.com/api/Contacts?where=AccountNumber==\"12345\""):
        contactID = get_xero_ContactID(code)

    assert contactID == mock_contactID


def test_get_xero_ContactID_no_contact():
    code = "12345"
    mock_response = {
        "Contacts": []
    }

    with patch(f'{MODULE_NAME}.__xero_get', return_value=mock_response), \
            patch(f'{MODULE_NAME}.construct_url',
                  return_value="http://api.xero.com/api/Contacts?where=AccountNumber==\"12345\""):
        contactID = get_xero_ContactID(code)

    assert contactID is None


def test_get_xero_ContactID_no_code():
    code = None
    mock_response = {
        "Contacts": [
            {"ContactID": "contact_12345"}
        ]
    }

    with patch(f'{MODULE_NAME}.__xero_get', return_value=mock_response), \
            patch(f'{MODULE_NAME}.construct_url',
                  return_value="http://api.xero.com/api/Contacts?where=AccountNumber==\"None\""):
        contactID = get_xero_ContactID(code)

    assert contactID == "contact_12345"


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
