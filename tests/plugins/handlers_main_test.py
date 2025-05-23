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
        "• Mobile: **[+1234567890](https://wa.me/+1234567890)**\n"
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

import unittest
from unittest.mock import patch, AsyncMock

# Import the handler to be tested
from plugins.handlers_main import member_search_cmd_handler

# --- New Async Test Class for member_search_cmd_handler ---

class TestMemberSearchCmdHandlerPersonCode(unittest.IsolatedAsyncioTestCase):

    @patch('stoscbots.util.utils.send_profile_address_and_pic', new_callable=AsyncMock)
    @patch('stoscbots.util.utils.generate_profile_msg_for_family')
    @patch('stoscbots.db.db.get_member_details', new_callable=AsyncMock)
    @patch('stoscbots.util.utils.is_valid_member_code')
    async def test_member_search_cmd_handler_with_person_code_success(
        self, 
        mock_is_valid_member_code, 
        mock_get_member_details, 
        mock_generate_profile_msg, 
        mock_send_profile_address_and_pic # Corrected mock name
    ):
        # Arrange
        sample_person_code = "P123"
        mock_is_valid_member_code.return_value = True

        # Prepare mock_db_result_tuple with 30 elements
        mock_db_result_list = [None] * 30
        mock_db_result_list[2] = "Smith Family"  # Example family name for generate_profile_msg
        mock_db_result_list[24] = "T999"        # target_per_ID
        mock_db_result_list[25] = "Target Person Name"  # target_per_FullName
        mock_db_result_tuple = tuple(mock_db_result_list)
        
        mock_db_result_for_call = [mock_db_result_tuple] # Function expects a list of tuples
        mock_get_member_details.return_value = mock_db_result_for_call
        
        mock_generate_profile_msg.return_value = "Test Profile Message"
        
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.command = ["u", sample_person_code]
        # mock_message.from_user is an AsyncMock by default. Set its id attribute.
        mock_message.from_user.id = 12345

        # Act
        await member_search_cmd_handler(mock_client, mock_message)

        # Assert
        mock_is_valid_member_code.assert_called_once_with(sample_person_code) # Verifying this mock is called
        mock_get_member_details.assert_called_once_with(sample_person_code, "code")
        mock_generate_profile_msg.assert_called_once_with(mock_db_result_for_call)
        mock_send_profile_address_and_pic.assert_called_once_with(
            mock_client,
            mock_message,
            "Test Profile Message",
            mock_db_result_for_call,
            searched_person=str(mock_db_result_tuple[24]),
            searched_person_name=mock_db_result_tuple[25]
        )

    @patch('stoscbots.util.utils.send_profile_address_and_pic', new_callable=AsyncMock)
    @patch('stoscbots.util.utils.generate_profile_msg_for_family')
    @patch('stoscbots.db.db.get_member_details', new_callable=AsyncMock)
    @patch('stoscbots.util.utils.is_valid_member_code')
    async def test_member_search_cmd_handler_person_code_not_enough_columns(
        self, 
        mock_is_valid_member_code, 
        mock_get_member_details, 
        mock_generate_profile_msg, 
        mock_send_profile_address_and_pic # Corrected mock name
    ):
        # Arrange
        sample_person_code = "P456"
        mock_is_valid_member_code.return_value = True

        mock_db_result_list_short = [None] * 10 # Fewer than 26 columns
        mock_db_result_list_short[2] = "Short Family"
        mock_db_result_tuple_short = tuple(mock_db_result_list_short)
        
        mock_db_result_for_call = [mock_db_result_tuple_short]
        mock_get_member_details.return_value = mock_db_result_for_call
        
        mock_generate_profile_msg.return_value = "Test Profile Message Short" # For clarity in test
        
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.command = ["u", sample_person_code]
        mock_message.from_user.id = 12345

        # Act
        await member_search_cmd_handler(mock_client, mock_message)

        # Assert
        mock_is_valid_member_code.assert_called_once_with(sample_person_code) # Verifying this mock
        mock_get_member_details.assert_called_once_with(sample_person_code, "code")
        mock_generate_profile_msg.assert_called_once_with(mock_db_result_for_call)
        mock_send_profile_address_and_pic.assert_called_once_with(
            mock_client,
            mock_message,
            "Test Profile Message Short",
            mock_db_result_for_call,
            searched_person=None,
            searched_person_name=None
        )

    @patch('stoscbots.util.utils.send_profile_address_and_pic', new_callable=AsyncMock)
    @patch('stoscbots.util.utils.generate_profile_msg_for_family') 
    @patch('stoscbots.db.db.get_member_details', new_callable=AsyncMock)
    @patch('stoscbots.util.utils.is_valid_member_code')
    async def test_member_search_cmd_handler_person_code_no_result(
        self, 
        mock_is_valid_member_code, 
        mock_get_member_details, 
        mock_generate_profile_msg, 
        mock_send_profile_address_and_pic # Corrected mock name
    ):
        # Arrange
        sample_person_code = "P404"
        mock_is_valid_member_code.return_value = True
        
        mock_get_member_details.return_value = [] # Empty list for no result
        
        mock_client = AsyncMock() 
        mock_message = AsyncMock()
        mock_message.command = ["u", sample_person_code]
        mock_message.from_user.id = 12345
        # mock_message.reply_text is an AsyncMock by default because mock_message is an AsyncMock

        # Act
        await member_search_cmd_handler(mock_client, mock_message)

        # Assert
        mock_is_valid_member_code.assert_called_once_with(sample_person_code) # Verifying this mock
        mock_get_member_details.assert_called_once_with(sample_person_code, "code")
        mock_message.reply_text.assert_called_once_with("No such Member", quote=True)
        mock_generate_profile_msg.assert_not_called() 
        mock_send_profile_address_and_pic.assert_not_called()

# To allow running tests from the command line (optional, if not using a test runner like pytest)
if __name__ == '__main__':
    unittest.main()

def test_generate_profile_msg_for_family_no_mobile():
    # Sample input
    result = [[
        "", "Head", "Smith", "smith@email.com", "", "spouse@email.com", "Jane", "jane@email.com",
        "2", "Uncle, Aunt", "123 Street", "City", "State", "", "0987654321",
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