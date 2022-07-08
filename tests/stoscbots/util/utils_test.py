import os 
from stoscbots.util import utils
from decimal import Decimal

VIBIN_TELEGRAM_ID = os.environ.get('VIBIN_TELEGRAM_ID')

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
    x = utils.generate_profile_msg(result)
    assert (
        "• Name: **John Mathai (A001)**\n• DOB: **1979-12-25**\n• Spouse: **John Wife**\n• Spouse DOB: **1985-12-25**\n• Children: **Johnson**\n• Other family members: **John Mother**\n• Add: **Address 1****, Address 2**, **547777**\n• Mobile: [99999999](tel://99999999)\n• Home: [66666666](tel://66666666)\n• Email: **john@example.com**\n• Spouse Email: **john_wife@example.com**\n• Home Parish: **Home Parish**\n• Membership Date: **2005-07-05**\n• Related Families: **A003**\n• Electoral Roll: **true**\n• Prayer Group: **Houg|Sengk|Pungg**\n"
        == x
    )


def test_generate_msg_xero_member_payments_2020():
    result = utils.generate_msg_xero_member_payments(name="John", _member_code="V019", _year="2020")
    expected = "**John**\n`For Year 2020`\n➖➖➖➖➖➖➖\n► Birthday Offering: **$30**\n► Christmas Offering: **$70**\n► Annual Thanksgiving Auction: **$1265**\n\n`As of: 30/04/2021 18:23`"
    assert expected == result


def test_get_member_payments():
    result = utils.get_member_payments(_member_code="V019", _year="2020")
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
