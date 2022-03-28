from pyrogram.types.bots_and_keyboards import CallbackQuery
from pyrogram.types import User
from stoscbots.util import utils
from pyrogram.types import Message, Chat
import pytest
import os
from pyrogram import Client

telegram_client = Client("my_account")
telegram_member_non = User(id="9999999999", first_name="Non-Member", username="non_member")
telegram_member_mc = User(id=os.environ.get("VIBIN_TELEGRAM_ID"), first_name="MC", username="mc_member")
telegram_member_smo = User(id="9999999991", first_name="SMO", username="smo")
telegram_member_area_prayer_coordinator = User(id="9999999992", first_name="APC", username="area_prayer_coordinator")
telegram_member_stmarys = User(id="9999999993", first_name="StMarys", username="stmarys")
telegram_member_harvest_admin = User(id="9999999994", first_name="HarvestAdmin", username="harvest_admin")
telegram_member_normal = User(id="9999999995", first_name="Member", username="member")
chat_bot = Chat(id="chat_id_123", type="bot")
msg = Message(message_id="msg_id_123", chat=chat_bot, client=telegram_client)

# Any arguments may be passed and mock_query_answer_with_data() will always return our
# mocked object, which only has the .query() method.
def mock_None_return(*args, **kwargs):
    return None


def mock_msg_reply(*args, **kwargs):
    return "Mock Message"


@pytest.fixture(autouse=True)
def mock_query_answer_with_data(monkeypatch):
    # apply the monkeypatch for query.answer() to mock_query_answer
    monkeypatch.setattr(CallbackQuery, "answer", mock_None_return)
    # apply the monkeypatch not to send any Telegram message
    monkeypatch.setattr(utils, "edit_and_send_msg", mock_None_return)
    monkeypatch.setattr(utils, "generate_msg_xero_member_payments", mock_None_return)
    monkeypatch.setattr(utils, "send_profile_address_and_pic", mock_None_return)
    monkeypatch.setattr(Client, "send_message", mock_msg_reply)
    monkeypatch.setattr(Client, "send_sticker", mock_msg_reply)
    # TODO These are shortcuts to Client.send_XXX but seems to be needed to ne neutered
    monkeypatch.setattr(Message, "reply", mock_msg_reply)
    monkeypatch.setattr(Message, "reply_sticker", mock_msg_reply)
    monkeypatch.setattr(Message, "reply_text", mock_msg_reply)
