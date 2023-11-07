from plugins import handlers_main
from stoscbots.util.utils import generate_profile_msg_for_family
from tests.mocks import *


def test_start_handler(monkeypatch):
    msg.command = ["start"]
    msg.from_user = telegram_member_mc
    handlers_main.start_handler(telegram_client, msg)
    assert 1 == 1


def test_start_handler_invalid_member(monkeypatch):
    msg.command = ["start"]
    msg.from_user = telegram_member_non
    handlers_main.start_handler(telegram_client, msg)
    assert 1 == 1


def test_generate_profile_msg_for_family():
    # Sample input
    result = [[
        "", "Head", "Smith", "smith@email.com", "", "spouse@email.com", "Jane", "jane@email.com",
        "2", "Uncle, Aunt", "123 Street", "City", "State", "1234567890", "0987654321",
        "St. Peter", "01-01-2020", "Jones", "Yes", "Group A", "01-01-1980", "01-01-1985"
    ]]

    # Expected output
    expected_msg = (
        "• Family: **Smith (Head)**\n"
        "• DOB: **01-01-1980**\n"
        "• Spouse: **Jane**\n"
        "• Spouse DOB: **01-01-1985**\n"
        "• Children: **2**\n"
        "• Other family members: **Uncle, Aunt**\n"
        "• Add: **123 Street**, **City**, **State**\n"
        "• Mobile: **[1234567890](https://wa.me/+1234567890)**\n"
        "• Home: [0987654321](tel://0987654321)\n"
        "• Email: **smith@email.com**\n"
        "• Spouse Email: **jane@email.com**\n"
        "• Home Parish: **St. Peter**\n"
        "• Membership Date: **01-01-2020**\n"
        "• Related Families: **Jones**\n"
        "• Electoral Roll: **Yes**\n"
        "• Prayer Group: **Group A**\n"
    )

    # Call the function
    msg = generate_profile_msg_for_family(result)

    # Assert that the generated message matches the expected message
    assert msg == expected_msg
