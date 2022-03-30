from pyrogram.types.bots_and_keyboards import CallbackQuery
from plugins import handlers_main
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
