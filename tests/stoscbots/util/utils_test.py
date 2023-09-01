import os
from decimal import Decimal
from unittest.mock import patch

import pytest

from stoscbots.util import utils

VIBIN_TELEGRAM_ID = int(os.environ.get('VIBIN_TELEGRAM_ID'))


def test_getMemberCode_from_TelegramID_Bad_value():
    memberCode = utils.getMemberCode_from_TelegramID("wrongID")
    assert memberCode is None


def test_getMemberCode_from_TelegramID():
    memberCode = utils.getMemberCode_from_TelegramID(VIBIN_TELEGRAM_ID)
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
            "• Family: **John Mathai (A001)**\n• DOB: **1979-12-25**\n• Spouse: **John Wife**\n• Spouse DOB: **1985-12-25**\n• Children: **Johnson**\n• Other family members: **John Mother**\n• Add: **Address 1**, **Address 2**, **547777**\n• Mobile: [99999999](tel://99999999)\n• Home: [66666666](tel://66666666)\n• Email: **john@example.com**\n• Spouse Email: **john_wife@example.com**\n• Home Parish: **Home Parish**\n• Membership Date: **2005-07-05**\n• Related Families: **A003**\n• Electoral Roll: **true**\n• Prayer Group: **Houg|Sengk|Pungg**\n"
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
            "modfied_ts": "30/04/2021 18:23:43",
            "AccountCode": "2020_3050",
        },
        {
            "ContactID": "23c1849f-01b3-46fd-80b7-846a5c03b1ef",
            "Account": "Christmas Offering",
            "ContactName": "Vibin Joseph Kuriakose",
            "LineAmount": Decimal("70"),
            "modfied_ts": "30/04/2021 18:23:43",
            "AccountCode": "2020_3090",
        },
        {
            "ContactID": "23c1849f-01b3-46fd-80b7-846a5c03b1ef",
            "Account": "Annual Thanksgiving Auction",
            "ContactName": "Vibin Joseph Kuriakose",
            "LineAmount": Decimal("1265"),
            "modfied_ts": "30/04/2021 18:23:43",
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


def test_is_valid_member_code_valid():
    result = utils.is_valid_member_code("V123")
    assert result


def test_is_valid_member_code_invalid_1():
    result = utils.is_valid_member_code("V12")
    assert result is False


def test_is_valid_member_code_invalid_2():
    result = utils.is_valid_member_code("V1234")
    assert result is False


def test_is_valid_member_code_invalid_3():
    result = utils.is_valid_member_code("V")
    assert result is False


def test_is_valid_member_code_invalid_4():
    result = utils.is_valid_member_code("")
    assert result is False


def test_is_valid_member_code_invalid_5():
    result = utils.is_valid_member_code("V12C")
    assert result is False


def test_is_valid_email():
    result = utils.is_valid_email("sample@example.com")
    assert result


def test_is_valid_email_invalid_1():
    result = utils.is_valid_email("abc")
    assert result is False


def test_is_valid_email_invalid_2():
    result = utils.is_valid_email("abc@")
    assert result is False


def test_is_valid_year():
    result = utils.is_valid_year("2004")
    assert result


def test_is_valid_year_invalid_1():
    result = utils.is_valid_year("04")
    assert result is False


def test_is_valid_year_invalid_2():
    result = utils.is_valid_year("20014")
    assert result is False


def test_is_valid_year_invalid_1():
    result = utils.is_valid_year("abcd")
    assert result is False


# Mocking the get_member_payments function
def mock_get_member_payments(member_code, year):
    if member_code == "12345" and year == "2023":
        return [
            {"Account": "Account1", "LineAmount": "100.00", "modfied_ts": "2023-08-31 12:00:00"},
            {"Account": "Account2", "LineAmount": "200.00", "modfied_ts": "2023-08-31 14:00:00"}
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