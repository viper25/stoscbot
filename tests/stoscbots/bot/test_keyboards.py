from datetime import date
from unittest import mock

import pytest
from pyrogram.types import InlineKeyboardButton

from stoscbots.bot import keyboards


# Test cases for get_icon function
@pytest.mark.parametrize("item, expected_icon", [
    ((528, 'X040', 'Jackson John', 'sam.x@gmail.com', 'Jackson John', 'example@example.com', 'Divya Sara Jackson',
      'example@hotmail.com', 'Enikka Jackson,Keith Jackson', None, '123C Kim Tian Road', '#01-111 Joe Tian Green',
      '545587',
      '99999999', '', 'St. Johns Orthodox Cathedral, Puthupally\r\nMavelikkara.', '2010-09-18', '', 'false', 'Central',
      '1979-12-14', '1983-07-23', 1, 1, 'Jackson John', 920), '⚡🧔🏻'),
    # Testing for head of family with different age groups and genders
    ((1, 'A001', 'Test User1', 'test1@example.com', 'Test User1', 'test1@example.com', 'Spouse1', 'spouse1@example.com',
      'Child1,Child2', None, '123 Test Street', '#01-01', '123456', '12345678', '', 'Test Church1', '2000-01-01', '',
      'false', 'Region1', '2005-04-10', '2007-05-15', 1, 1, 'Test User1', 101), '⚡🧔🏻'),
    ((2, 'A002', 'Test User2', 'test2@example.com', 'Test User2', 'test2@example.com', 'Spouse2', 'spouse2@example.com',
      'Child3,Child4', None, '456 Test Avenue', '#02-02', '654321', '87654321', '', 'Test Church2', '1995-02-02', '',
      'false', 'Region2', f'{date.today().year - 19}-06-20', '1983-07-23', 2, 1, 'Test User2', 102), '⚡👩🏻'),
    # Testing for non-head of family with different age groups and genders
    ((3, 'A003', 'Test User3', 'test3@example.com', 'Test User3', 'test3@example.com', 'Spouse3', 'spouse3@example.com',
      'Child5,Child6', None, '789 Test Road', '#03-03', '789123', '12347890', '', 'Test Church3', '1990-03-03', '',
      'false', 'Region3', f'{date.today().year - 25}-08-15', f'{date.today().year - 27}-09-18', 1, 0, 'Test User3',
      103), '🧔🏻'),
    ((4, 'A004', 'Test User4', 'test4@example.com', 'Test User4', 'test4@example.com', 'Spouse4', 'spouse4@example.com',
      'Child7,Child8', None, '101 Test Lane', '#04-04', '101112', '98765432', '', 'Test Church4', '1985-04-04', '',
      'false', 'Region4', None, f'{date.today().year - 30}-10-20', 2, 0, 'Test User4', 104), '♀'),
    # Testing for individuals with no age data but with gender data
    ((5, 'A005', 'Test User5', 'test5@example.com', 'Test User5', 'test5@example.com', 'Spouse5', 'spouse5@example.com',
      'Child9,Child10', None, '202 Test Drive', '#05-05', '202203', '56789012', '', 'Test Church5', '1980-05-05', '',
      'false', 'Region5', None, None, 1, 0, 'Test User5', 105), '♂'),
])
def test_get_icon(item, expected_icon):
    assert keyboards.get_icon(item) == expected_icon


@pytest.mark.parametrize(
    "results, expected",
    [
        # Test case 2: List with a single item
        ([
             (1, 'A001', 'Test User', 'test@example.com', 'Test User', 'test@example.com', 'Test Spouse',
              'spouse@example.com', 'Test Child1,Test Child2', None, '123 Test Street', '#123 Test Building', '123456',
              '12345678', '', 'Test Church', '2000-01-01', '', 'false', 'Test Area', '1980-01-01', '1985-01-01', 1, 1,
              'Test User', 1000)
         ], [
             [InlineKeyboardButton(
                 text=f"{keyboards.get_icon((1, 'A001', 'Test User', 'test@example.com', 'Test User', 'test@example.com', 'Test Spouse', 'spouse@example.com', 'Test Child1,Test Child2', None, '123 Test Street', '#123 Test Building', '123456', '12345678', '', 'Test Church', '2000-01-01', '', 'false', 'Test Area', '1980-01-01', '1985-01-01', 1, 1, 'Test User', 1000))} Test User (A001) »",
                 callback_data="Member_A001_1000"),
                 InlineKeyboardButton(text='🔙 Return to Main menu', callback_data='Main Menu')]
         ]),

        # Test case 3: List with an even number of items
        ([
             (1, 'A001', 'Test User1', 'test1@example.com', 'Test User1', 'test1@example.com', 'Test Spouse1',
              'spouse1@example.com', 'Test Child1,Test Child2', None, '123 Test Street', '#123 Test Building', '123456',
              '12345678', '', 'Test Church1', '2000-01-01', '', 'false', 'Test Area', '1980-01-01', '1985-01-01', 1, 1,
              'Test User1', 1000),
             (2, 'A002', 'Test User2', 'test2@example.com', 'Test User2', 'test2@example.com', 'Test Spouse2',
              'spouse2@example.com', 'Test Child3,Test Child4', None, '456 Test Street', '#456 Test Building', '654321',
              '87654321', '', 'Test Church2', '2005-01-01', '', 'true', 'Test Area', '1990-01-01', '1995-01-01', 2, 2,
              'Test User2', 2000)
         ], [
             [
                 InlineKeyboardButton(
                     text=f"{keyboards.get_icon((1, 'A001', 'Test User1', 'test1@example.com', 'Test User1', 'test1@example.com', 'Test Spouse1', 'spouse1@example.com', 'Test Child1,Test Child2', None, '123 Test Street', '#123 Test Building', '123456', '12345678', '', 'Test Church1', '2000-01-01', '', 'false', 'Test Area', '1980-01-01', '1985-01-01', 1, 1, 'Test User1', 1000))} Test User1 (A001) »",
                     callback_data="Member_A001_1000"),
                 InlineKeyboardButton(
                     text=f"{keyboards.get_icon((2, 'A002', 'Test User2', 'test2@example.com', 'Test User2', 'test2@example.com', 'Test Spouse2', 'spouse2@example.com', 'Test Child3,Test Child4', None, '456 Test Street', '#456 Test Building', '654321', '87654321', '', 'Test Church2', '2005-01-01', '', 'true', 'Test Area', '1990-01-01', '1995-01-01', 2, 2, 'Test User2', 2000))} Test User2 (A002) »",
                     callback_data="Member_A002_2000")
             ],
             [InlineKeyboardButton(text='🔙 Return to Main menu', callback_data='Main Menu')]
         ]),

        # Test case 4: List with an odd number of items
        ([
             (1, 'A001', 'Test User1', 'test1@example.com', 'Test User1', 'test1@example.com', 'Test Spouse1',
              'spouse1@example.com', 'Test Child1,Test Child2', None, '123 Test Street', '#123 Test Building', '123456',
              '12345678', '', 'Test Church1', '2000-01-01', '', 'false', 'Test Area', '1980-01-01', '1985-01-01', 1, 1,
              'Test User1', 1000),
             (2, 'A002', 'Test User2', 'test2@example.com', 'Test User2', 'test2@example.com', 'Test Spouse2',
              'spouse2@example.com', 'Test Child3,Test Child4', None, '456 Test Street', '#456 Test Building', '654321',
              '87654321', '', 'Test Church2', '2005-01-01', '', 'true', 'Test Area', '1990-01-01', '1995-01-01', 2, 2,
              'Test User2', 2000),
             (3, 'A003', 'Test User3', 'test3@example.com', 'Test User3', 'test3@example.com', 'Test Spouse3',
              'spouse3@example.com', 'Test Child5,Test Child6', None, '789 Test Street', '#789 Test Building', '789123',
              '78912345', '', 'Test Church3', '2010-01-01', '', 'false', 'Test Area', '2000-01-01', '2005-01-01', 3, 3,
              'Test User3', 3000)
         ], [
             [
                 InlineKeyboardButton(
                     text=f"{keyboards.get_icon((1, 'A001', 'Test User1', 'test1@example.com', 'Test User1', 'test1@example.com', 'Test Spouse1', 'spouse1@example.com', 'Test Child1,Test Child2', None, '123 Test Street', '#123 Test Building', '123456', '12345678', '', 'Test Church1', '2000-01-01', '', 'false', 'Test Area', '1980-01-01', '1985-01-01', 1, 1, 'Test User1', 1000))} Test User1 (A001) »",
                     callback_data="Member_A001_1000"),
                 InlineKeyboardButton(
                     text=f"{keyboards.get_icon((2, 'A002', 'Test User2', 'test2@example.com', 'Test User2', 'test2@example.com', 'Test Spouse2', 'spouse2@example.com', 'Test Child3,Test Child4', None, '456 Test Street', '#456 Test Building', '654321', '87654321', '', 'Test Church2', '2005-01-01', '', 'true', 'Test Area', '1990-01-01', '1995-01-01', 2, 2, 'Test User2', 2000))} Test User2 (A002) »",
                     callback_data="Member_A002_2000")
             ],
             [
                 InlineKeyboardButton(
                     text=f"{keyboards.get_icon((3, 'A003', 'Test User3', 'test3@example.com', 'Test User3', 'test3@example.com', 'Test Spouse3', 'spouse3@example.com', 'Test Child5,Test Child6', None, '789 Test Street', '#789 Test Building', '789123', '78912345', '', 'Test Church3', '2010-01-01', '', 'false', 'Test Area', '2000-01-01', '2005-01-01', 3, 3, 'Test User3', 3000))} Test User3 (A003) »",
                     callback_data="Member_A003_3000")
                 ,
                 InlineKeyboardButton(text='🔙 Return to Main menu', callback_data='Main Menu')]
         ])
    ]
)
def test_get_member_listing_keyboard(results, expected):
    assert keyboards.get_member_listing_keyboard(results).inline_keyboard == expected


def test_create_button():
    # Test 1: Create button without web_app parameter
    button = keyboards.create_button("Test Button", "TEST_CALLBACK")
    assert button.text == "Test Button"
    assert button.callback_data == "TEST_CALLBACK"
    assert button.web_app is None

    # Test 2: Create button with web_app parameter
    web_app = keyboards.WebAppInfo(url="https://example.com")
    button = keyboards.create_button("Test Button with Web App", "TEST_CALLBACK", web_app)
    assert button.text == "Test Button with Web App"
    assert button.callback_data == "TEST_CALLBACK"
    assert button.web_app == web_app


def test_get_main_keyboard():
    with mock.patch('stoscbots.util.bot_auth.is_mgmt_member') as mock_mgmt_member:
        # Test 1: Management member keyboard
        mock_mgmt_member.return_value = True
        keyboard = keyboards.get_main_keyboard('mgmt')
        assert len(keyboard.inline_keyboard) == 4  # Adjust based on the expected number of rows

        # Test 2: Normal member keyboard
        mock_mgmt_member.return_value = False
        keyboard = keyboards.get_main_keyboard('normal')
        assert len(keyboard.inline_keyboard) == 3  # Adjust based on the expected number of rows


def test_get_services_keyboard():
    keyboard = keyboards.get_services_keyboard()

    assert isinstance(keyboard,
                      keyboards.InlineKeyboardMarkup), "The return type should be an InlineKeyboardMarkup instance"

    assert len(keyboard.inline_keyboard) == 1, "The keyboard should have one row"

    row = keyboard.inline_keyboard[0]
    assert len(row) == 2, "The row should have two buttons"

    back_to_main_button, prayer_requests_listing_button = row

    assert isinstance(back_to_main_button,
                      InlineKeyboardButton), "The first button should be an InlineKeyboardButton instance"
    assert back_to_main_button.callback_data == "Main Menu", "The first button's callback data should be 'Main Menu'"
    assert back_to_main_button.text == "🔙 Return to Main menu", "The first button's text should be '🔙 Return to Main menu'"

    assert isinstance(prayer_requests_listing_button,
                      InlineKeyboardButton), "The second button should be an InlineKeyboardButton instance"
    assert prayer_requests_listing_button.callback_data == "Prayer Requests", "The second button's callback data should be 'Prayer Requests'"
    assert prayer_requests_listing_button.text == "📿 Prayer Requests", "The second button's text should be '📿 Prayer Requests'"
