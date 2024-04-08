from decimal import Decimal
from unittest.mock import patch, AsyncMock, mock_open, MagicMock

import pandas as pd
import pytest

from stoscbots.util import utils
from stoscbots.util.utils import format_telegram_message, get_telegram_file_url, upload_to_s3_and_get_url
from tests.stoscbots.util import bot_auth_test


def test_getMemberCode_from_TelegramID_Bad_value():
    memberCode = utils.getMemberCode_from_TelegramID("wrongID")
    assert memberCode is None


# We assume the SUPER ADMIN is always a member = V019
def test_getMemberCode_from_TelegramID():
    memberCode = utils.getMemberCode_from_TelegramID(bot_auth_test.get_super_admin_id())
    assert memberCode == "V019"


def test_get_address_details():
    x = utils.get_address_details("543316")
    assert x[0] == "1.39316162628404"
    assert x[1] == "103.888370952522"


def test_generate_profile_msg():
    result = [
        (
            587,
            "A001",
            "John Mathai",
            "john@example.com",
            "John mathai",
            "john@example.com",
            "John Wife",
            "john_wife@example.com",
            "Johnson",
            "John Mother",
            "Address 1",
            "Address 2",
            "547777",
            "99999999",
            "66666666",
            "Home Parish",
            "2005-07-05",
            "A003",
            "true",
            "Houg|Sengk|Pungg",
            "1979-12-25",
            "1985-12-25",
        )
    ]
    x = utils.generate_profile_msg_for_family(result)
    assert (
            "• Family: **John Mathai (A001)**\n• DOB: **1979-12-25**\n• Spouse: **John Wife**\n• Spouse DOB: **1985-12-25**\n• Children: **Johnson**\n• Other family members: **John Mother**\n• Add: **Address 1**, **Address 2**, **547777**\n• Mobile: **[99999999](https://wa.me/+6599999999)**\n• Home: [66666666](tel://66666666)\n• Email: **john@example.com**\n• Spouse Email: **john_wife@example.com**\n• Home Parish: **Home Parish**\n• Membership Date: **2005-07-05**\n• Related Families: **A003**\n• Electoral Roll: **true**\n• Prayer Group: **Houg|Sengk|Pungg**\n"
            == x
    )


def test_generate_msg_xero_member_payments_2020():
    result = utils.generate_msg_xero_member_payments(name="John", member_code="V019", year="2020")
    expected = "**John**\n`For Year 2020`\n➖➖➖➖➖➖➖\n► Birthday Offering: **$30**\n► Christmas Offering: **$70**\n► Annual Thanksgiving Auction: **$1265**\n\n`As of: 30/04/2021 18:23`"
    assert expected == result


def test_get_member_payments():
    result = utils.get_member_payments(member_code="V019", year="2020")
    expected = [
        {
            "ContactID": "23c1849f-01b3-46fd-80b7-846a5c03b1ef",
            "Account": "Birthday Offering",
            "ContactName": "Vibin Joseph Kuriakose",
            "LineAmount": Decimal("30"),
            "modified_ts": "30/04/2021 18:23:43",
            "AccountCode": "2020_3050",
        },
        {
            "ContactID": "23c1849f-01b3-46fd-80b7-846a5c03b1ef",
            "Account": "Christmas Offering",
            "ContactName": "Vibin Joseph Kuriakose",
            "LineAmount": Decimal("70"),
            "modified_ts": "30/04/2021 18:23:43",
            "AccountCode": "2020_3090",
        },
        {
            "ContactID": "23c1849f-01b3-46fd-80b7-846a5c03b1ef",
            "Account": "Annual Thanksgiving Auction",
            "ContactName": "Vibin Joseph Kuriakose",
            "LineAmount": Decimal("1265"),
            "modified_ts": "30/04/2021 18:23:43",
            "AccountCode": "2020_3200",
        },
    ]
    assert expected == result


def test_get_member_payments_1():
    # Mocking the xero_utils.get_xero_ContactID method
    with patch('stoscbots.xero.xero_utils.get_xero_ContactID') as mock_get_contact_id:
        # Mocking the table_member_payments.query method
        with patch('stoscbots.util.utils.table_member_payments.query') as mock_query:
            # Test when contact_id is None
            mock_get_contact_id.return_value = None
            result = utils.get_member_payments("test_code", "2023")
            assert result is None

            # Test when contact_id is not None and there are items in response
            mock_get_contact_id.return_value = "12345"
            mock_query.return_value = {'Items': ['item1', 'item2']}
            result = utils.get_member_payments("test_code", "2023")
            assert result == ['item1', 'item2']

            # Test when contact_id is not None and there are no items in response
            mock_get_contact_id.return_value = "12345"
            mock_query.return_value = {'Items': []}
            result = utils.get_member_payments("test_code", "2023")
            assert result == []


# ------------------------------------------------------------
def test_valid_member_codesis_valid_member_code():
    valid_codes = ["V019", "A023", "Z999", "W001"]
    for code in valid_codes:
        assert utils.is_valid_member_code(code) == True, f"Expected {code} to be valid"


def test_is_valid_member_code_invalid():
    invalid_codes = [
        "",  # Empty string
        "V01",  # Too short
        "V0199",  # Too long
        "019V",  # Starts with a number
        "VV19",  # Starts with two letters
        "V01A",  # Ends with a letter
        "V0A9",  # Contains a letter in the middle
        "V0 9",  # Contains a space
        "V0@9"  # Contains a special character
    ]
    for code in invalid_codes:
        assert utils.is_valid_member_code(code) == False, f"Expected {code} to be invalid"


# ------------------------------------------------------------
def test_valid_email():
    assert utils.is_valid_email("test@example.com") == True
    assert utils.is_valid_email("test.email+filter@example.co.uk") == True


def test_invalid_email():
    assert utils.is_valid_email("") == False
    assert utils.is_valid_email("test") == False
    assert utils.is_valid_email("test@.com") == False
    assert utils.is_valid_email("test@com") == False
    assert utils.is_valid_email("@example.com") == False
    assert utils.is_valid_email("test@example") == False
    assert utils.is_valid_email("test@example..com") == False


def test_none_email():
    assert utils.is_valid_email(None) == False


# ------------------------------------------------------------
@pytest.mark.parametrize("year, expected", [
    ("2023", True),
    ("0000", True),
    ("abcd", False),
    ("12345", False),
    ("123", False),
    ("", False),
    (" 2023", False),
    ("2023 ", False),
    ("20 23", False),
    (2023, False)  # Testing an integer input
])
def test_is_valid_year(year, expected):
    assert utils.is_valid_year(year) == expected


# ------------------------------------------------------------
# Mocking the get_member_payments function
def mock_get_member_payments(member_code, year):
    if member_code == "12345" and year == "2023":
        return [
            {"Account": "Account1", "LineAmount": "100.00", "modified_ts": "2023-08-31 12:00:00"},
            {"Account": "Account2", "LineAmount": "200.00", "modified_ts": "2023-08-31 14:00:00"}
        ]
    return []


@pytest.mark.parametrize(
    "name, member_code, year, expected_output",
    [
        ("John Doe", "12345", "2023",
         "**John Doe**\n`For Year 2023`\n➖➖➖➖➖➖➖\n► Account1: **$100.00**\n► Account2: **$200.00**\n\n`As of: 2023-08-31 14:00`"),
        ("Jane Doe", "67890", "2023", "No contributions for **Jane Doe** for year **2023**")
    ]
)
def test_generate_msg_xero_member_payments(name, member_code, year, expected_output, monkeypatch):
    # Patching the get_member_payments function with our mock
    monkeypatch.setattr("stoscbots.util.utils.get_member_payments", mock_get_member_payments)

    result = utils.generate_msg_xero_member_payments(name, member_code, year)
    assert result == expected_output


# ------------------------------------------------------------
def test_generate_msg_xero_member_invoices():
    member_code = "123"
    year = "2021"
    expected_output = "--**John Doe (123)**--\n\n**[INV-21-001] - ****$100.00**: DUE 🟠\n  `• Item 1-$50.00`\n  `• Item 2-$50.00`\n––––———————————————\n"
    # Mock the get_Invoices function to return test data
    invoices = {
        "Invoices": [
            {
                "Contact": {"Name": "John Doe"},
                "Type": "ACCREC",
                "InvoiceNumber": "INV-21-001",
                "AmountDue": 100.0,
                "Total": 100.0,
                "Status": "AUTHORISED",
                "DateString": "2021-01-01",
                "LineItems": [
                    {"Description": "Item 1", "LineAmount": 50.0},
                    {"Description": "Item 2", "LineAmount": 50.0},
                ],
            }
        ]
    }
    with patch("stoscbots.util.utils.xero_utils.get_Invoices", return_value=invoices):
        assert utils.generate_msg_xero_member_invoices(member_code, year) == expected_output


def test_generate_msg_xero_member_invoices_invalid_year():
    member_code = "123"
    year = "abcd"
    expected_output = "Not a valid year: **abcd**"
    with patch("stoscbots.util.utils.xero_utils.get_Invoices", return_value={}):
        assert utils.generate_msg_xero_member_invoices(member_code, year) == expected_output


def test_generate_msg_xero_member_invoices_no_invoices():
    member_code = "123"
    year = "2021"
    expected_output = "No invoices for 123"
    with patch("stoscbots.util.utils.xero_utils.get_Invoices", return_value={}):
        assert utils.generate_msg_xero_member_invoices(member_code, year) == expected_output


def test_generate_msg_xero_member_invoices_invoice_type_and_status():
    member_code = "123"
    year = "2021"
    # Test for ACCREC type and PAID status
    invoices = {
        "Invoices": [
            {
                "Contact": {"Name": "John Doe"},
                "Type": "ACCREC",
                "InvoiceNumber": "INV-21-001",
                "AmountDue": 0.0,
                "Total": 100.0,
                "Status": "PAID",
                "DateString": "2021-01-01",
                "LineItems": [
                    {"Description": "Item 1", "LineAmount": 50.0},
                    {"Description": "Item 2", "LineAmount": 50.0},
                ],
            }
        ]
    }
    expected_output = "--**John Doe (123)**--\n\n**[INV-21-001] - ****$100.00**: PAID 🟢\n  `• Item 1-$50.00`\n  `• Item 2-$50.00`\n––––———————————————\n"
    with patch("stoscbots.util.utils.xero_utils.get_Invoices", return_value=invoices):
        assert utils.generate_msg_xero_member_invoices(member_code, year) == expected_output

    # Test for ACCREC type and DRAFT status
    invoices["Invoices"][0]["Status"] = "DRAFT"
    expected_output = "--**John Doe (123)**--\n\n**[INV-21-001] - ****$100.00**: DRAFT 🟠\n  `• Item 1-$50.00`\n  `• Item 2-$50.00`\n––––———————————————\n"
    with patch("stoscbots.util.utils.xero_utils.get_Invoices", return_value=invoices):
        assert utils.generate_msg_xero_member_invoices(member_code, year) == expected_output


def test_generate_msg_xero_member_invoices_invoice_number_patterns():
    member_code = "123"
    year = "2021"
    # Test for HF-<year> pattern
    invoices = {
        "Invoices": [
            {
                "Contact": {"Name": "John Doe"},
                "Type": "ACCREC",
                "InvoiceNumber": "HF-21-001",
                "AmountDue": 100.0,
                "Total": 100.0,
                "Status": "AUTHORISED",
                "DateString": "2021-01-01",
                "LineItems": [
                    {"Description": "Item 1", "LineAmount": 50.0},
                    {"Description": "Item 2", "LineAmount": 50.0},
                ],
            }
        ]
    }
    expected_output = "--**John Doe (123)**--\n\n**[HF-21-001] - ****$100.00**: DUE 🟠\n  `• Item 1-$50.00`\n  `• Item 2-$50.00`\n––––———————————————\n"
    with patch("stoscbots.util.utils.xero_utils.get_Invoices", return_value=invoices):
        assert utils.generate_msg_xero_member_invoices(member_code, year) == expected_output


# ------------------------------------------------------------
# Mocking the table_stosc_harvest_contributors.query method
class MockTable:
    @staticmethod
    def query_with_items(KeyConditionExpression):
        # This is a mock response. Adjust as needed.
        return {
            'Items': [{
                'items': [
                    {'itemCode': '001', 'itemName': 'ItemA', 'winner': 'John', 'winning_bid': 100, 'bids': 5},
                    {'itemCode': '002', 'itemName': 'ItemB', 'winner': 'Doe', 'winning_bid': 200, 'bids': 10}
                ],
                'total_fetched': 300
            }]
        }

    @staticmethod
    def query_without_items(KeyConditionExpression):
        return {'Items': []}

    @staticmethod
    def query_raises_exception(KeyConditionExpression):
        raise Exception("Database error")


@pytest.fixture
def mock_table_with_items(monkeypatch):
    monkeypatch.setattr('stoscbots.util.utils.table_stosc_harvest_contributors.query', MockTable.query_with_items)


@pytest.fixture
def mock_table_without_items(monkeypatch):
    monkeypatch.setattr('stoscbots.util.utils.table_stosc_harvest_contributors.query', MockTable.query_without_items)


@pytest.fixture
def mock_table_raises_exception(monkeypatch):
    monkeypatch.setattr('stoscbots.util.utils.table_stosc_harvest_contributors.query', MockTable.query_raises_exception)


@pytest.fixture
def mock_table(monkeypatch):
    def mock_query(*args, **kwargs):
        return MockTable.query_with_items(*args, **kwargs)

    monkeypatch.setattr('stoscbots.util.utils.table_stosc_harvest_contributors.query', mock_query)


def test_generate_msg_member_auction_contributions(mock_table):
    member_code = "test_code"
    expected_output = (
        "**Auction Donations**\n"
        "➖➖➖➖➖➖➖\n"
        "Items Donated: 2\n"
        "———————\n"
        "[`001`] **ItemA**: John ($100) (5 bids)\n"
        "[`002`] **ItemB**: Doe ($200) (10 bids)\n"
        "———————\n"
        "Total sold for: **$300**"
    )
    result = utils.generate_msg_member_auction_contributions(member_code)
    assert result == expected_output


def test_generate_msg_with_items(mock_table_with_items):
    member_code = "test_code"
    expected_output = (
        "**Auction Donations**\n"
        "➖➖➖➖➖➖➖\n"
        "Items Donated: 2\n"
        "———————\n"
        "[`001`] **ItemA**: John ($100) (5 bids)\n"
        "[`002`] **ItemB**: Doe ($200) (10 bids)\n"
        "———————\n"
        "Total sold for: **$300**"
    )
    result = utils.generate_msg_member_auction_contributions(member_code)
    assert result == expected_output


def test_generate_msg_raises_exception(mock_table_raises_exception, caplog):
    member_code = "test_code"
    result = utils.generate_msg_member_auction_contributions(member_code)
    assert "Database error" in caplog.text
    assert result is None


# ------------------------------------------------------------

def test_generate_msg_member_auction_purchases_no_data():
    with patch('stoscbots.util.utils.table_stosc_harvest_winners.query', side_effect=Exception()):
        result = utils.generate_msg_member_auction_purchases("test_code")
        assert result == "No Data"


def test_generate_msg_member_auction_purchases_no_bids():
    mock_response = {'Items': []}
    with patch('stoscbots.util.utils.table_stosc_harvest_winners.query', return_value=mock_response):
        result = utils.generate_msg_member_auction_purchases("test_code")
        assert result == "~ No bids or purchases yet ~\n"


def test_generate_msg_member_auction_purchases_with_bids():
    mock_response = {
        'Items': [{
            'items': [
                {'itemCode': '001', 'itemName': 'TestItem', 'winning_bid': 1000, 'bids': 5},
            ],
            'total_bid': 1000
        }]
    }
    with patch('stoscbots.util.utils.table_stosc_harvest_winners.query', return_value=mock_response):
        result = utils.generate_msg_member_auction_purchases("test_code")
        expected_msg = (
            "**Auction Wins**\n"
            "➖➖➖➖➖➖➖\n"
            "Items Won: 1\n"
            "———————\n"
            "[`001`] **TestItem**: $1,000 (5 bids)\n"
            "———————\n"
            "Total: **$1,000**"
        )
        assert result == expected_msg


# ------------------------------------------------------------

@pytest.mark.asyncio
@patch('stoscbots.util.utils.get_address_details')
async def test_send_profile_address_and_pic(mock_get_address_details):
    # Mock client and callback query
    mock_client = AsyncMock()
    mock_query = AsyncMock()
    mock_query.from_user.id = 12345  # Mock user ID

    # Test scenario: Zip code present and no searched_person
    mock_get_address_details.return_value = (12.34, 56.78)  # Mock latitude and longitude
    # Mock result list
    result = [
        [
            123,  # ID
            'A001',  # Code
            'Alice Anderson',  # Full Name
            'alice@example.com',  # Email 1
            'Alice Anderson',  # Name 1
            'alice1@example.com',  # Email 2
            'Bob Anderson',  # Name 2
            'bob@example.com',  # Email 3
            'Charlie Anderson',  # Child Name
            None,  # Email 4
            '650 Yio Chu kang Road',  # Address 1
            '',  # Address 2
            '787075',  # Zip Code
            '12345678',  # Phone 1
            '87654321',  # Phone 2
            '',  # Church
            '',  # Baptism Date
            'B002',  # Child Code
            'true',  # Some Boolean Value
            'Mock|City|Area',  # Area
            '1990-01-01',  # Birthdate 1
            '1992-02-02',  # Birthdate 2
            1,  # Some Integer Value
            1  # Some Integer Value
        ],
    ]

    await utils.send_profile_address_and_pic(mock_client, mock_query, "test message", result)
    mock_client.send_venue.assert_called_once()
    mock_client.send_photo.assert_called_once()


# ------------------------------------------------------------
# Sample mock data
mock_data = {
    'Items': [
        {'Name': 'Project1', 'income': 100.50, 'expense': 50.25, 'modified_ts': '2023-08-30'},
        {'Name': 'Project2', 'income': 0, 'expense': 0, 'modified_ts': '2023-08-29'},
        {'Name': 'Project3', 'income': 200.00, 'expense': 150.00, 'modified_ts': '2023-08-31'}
    ]
}


def test_raw_data_true(monkeypatch):
    monkeypatch.setattr('stoscbots.util.utils.table_stosc_xero_accounts_tracking.scan', lambda: mock_data)
    result = utils.get_tracked_projects(raw_data=True)
    assert result == mock_data['Items']


def test_raw_data_false(monkeypatch):
    monkeypatch.setattr('stoscbots.util.utils.table_stosc_xero_accounts_tracking.scan', lambda: mock_data)
    result = utils.get_tracked_projects(raw_data=False)
    expected_output = (
        "**TRACKED PROJECTS**\n"
        "➖➖➖➖➖➖➖➖\n"
        "• Project1 - `$100.50` | `$50.25`\n"
        "• Project3 - `$200.00` | `$150.00`\n"
        "\n"
        "`As of: 2023-08-31`"
    )
    assert result == expected_output


def test_no_tracked_projects(monkeypatch):
    monkeypatch.setattr('stoscbots.util.utils.table_stosc_xero_accounts_tracking.scan', lambda: {'Items': []})
    result = utils.get_tracked_projects(raw_data=False)
    expected_output = (
        "**TRACKED PROJECTS**\n"
        "➖➖➖➖➖➖➖➖\n"
        "\n\n"
        "`As of: 0`"
    )
    assert result == expected_output


# ------------------------------------------------------------
def test_get_outstandings():
    # Expected markdown
    expected_output = (
        ('**OUTSTANDING DUES**\n'
         '➖➖➖➖➖➖➖➖\n'
         '\n'
         '`|    | Inv   | Total     | Due      |\n'
         '|---:|:------|:----------|:---------|\n'
         '|  0 | S-18  | $ 2,140   | $ 1,720  |\n'
         '|  1 | S-19  | $ 9,902   | $ 6,580  |\n'
         '|  2 | S-20  | $ 41,962  | $ 6,940  |\n'
         '|  3 | S-21  | $ 126,262 | $ 6,460  |\n'
         '|  4 | H-22  | $ 115,705 | $ 785    |\n'
         '|  5 | S-22  | $ 126,468 | $ 11,010 |\n'
         '|  6 | S-23  | $ 130,296 | $ 33,450 |`')
    )

    # Mock data to be returned by pickle.load
    mock_df = pd.DataFrame({
        'Inv': ['S-18', 'S-19', 'S-20', 'S-21', 'H-22', 'S-22', 'S-23'],
        'Total': ['$ 2,140', '$ 9,902', '$ 41,962', '$ 126,262', '$ 115,705', '$ 126,468', '$ 130,296'],
        'Due': ['$ 1,720', '$ 6,580', '$ 6,940', '$ 6,460', '$ 785', '$ 11,010', '$ 33,450']
    })

    # Mocking environment variable and file I/O
    with patch('os.environ.get', side_effect=['TEST', 'DUMMY_PATH']), \
            patch('builtins.open', mock_open()), \
            patch('pickle.load', return_value=mock_df):
        result = utils.get_outstandings()

    assert result == expected_output


# ------------------------------------------------------------
# Mock the DynamoDB call
@patch('stoscbots.util.utils.table_stosc_bot_member_telegram.query')
def test_get_telegram_id_found(mock_query):
    # Mock the response from DynamoDB
    mock_query.return_value = {
        'Items': [{'member_code': 'TEST123', 'telegram_id': '123456789'}]
    }

    result = utils.get_TelegramID_from_MemberCode('TEST123')
    assert result['telegram_id'] == '123456789'


@patch('stoscbots.util.utils.table_stosc_bot_member_telegram.query')
def test_get_telegram_id_not_found(mock_query):
    # Mock an empty response from DynamoDB
    mock_query.return_value = {'Items': []}

    result = utils.get_TelegramID_from_MemberCode('NONEXISTENT')
    assert result is None


@patch('stoscbots.util.utils.table_stosc_bot_member_telegram.query')
def test_get_telegram_id_error(mock_query, capfd):
    mock_query.side_effect = Exception("DynamoDB error")

    result = utils.get_TelegramID_from_MemberCode('TEST123')

    # Capture the printed output
    captured = capfd.readouterr()

    assert "Error fetching Telegram ID for member code TEST123: DynamoDB error" in captured.out
    assert result is None


# ------------------------------------------------------------

def test_format_telegram_message():
    msg = "a" * 4050
    assert format_telegram_message(msg) == msg

    msg = "a" * 4100
    assert format_telegram_message(msg) == ("a" * 4076 + '\n`... (truncated)`')


# ------------------------------------------------------------
@patch('os.environ.get')
@patch('requests.get')
@pytest.mark.asyncio
async def test_get_telegram_file_url(mock_get, mock_environ_get):
    # Arrange
    mock_environ_get.return_value = 'dummy_bot_token'
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'ok': True,
        'result': {
            'file_path': 'dummy_file_path'
        }
    }
    mock_get.return_value = mock_response
    dummy_photo = type('', (), {})()  # create a dummy object
    dummy_photo.file_id = 'dummy_file_id'

    # Act
    result = await get_telegram_file_url(dummy_photo)

    # Assert
    expected_url = 'https://api.telegram.org/file/botdummy_bot_token/dummy_file_path'
    assert result == expected_url


# ------------------------------------------------------------
@patch('os.environ.get')
@patch('boto3.resource')
def test_upload_to_s3_and_get_url(mock_boto3_resource, mock_environ_get):
    # Arrange
    mock_environ_get.return_value = 'dummy_aws_key'
    mock_s3_resource = MagicMock()
    mock_boto3_resource.return_value = mock_s3_resource
    mock_s3_object = MagicMock()
    mock_s3_resource.Object.return_value = mock_s3_object
    mock_s3_object.put.return_value = None  # Simulate successful upload
    dummy_image_file = MagicMock()
    dummy_image_file.name = 'dummy_image.jpg'
    dummy_object_name = 'dummy_object_name'
    mock_file = MagicMock()
    mock_file.read.return_value = b"file content"

    # Act
    with patch('builtins.open', mock_open(read_data='dummy data')) as mock_file:
        result = upload_to_s3_and_get_url(dummy_image_file, dummy_object_name)

    # Assert
    expected_url = 'https://stoscsg.s3.ap-southeast-1.amazonaws.com/dummy_object_name'
    assert result == expected_url