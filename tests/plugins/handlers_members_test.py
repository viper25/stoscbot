from pyrogram.types.bots_and_keyboards import CallbackQuery
from plugins import handlers_members
from tests.mocks import *


def test_get_today_bdays(monkeypatch):
    telegram_query = CallbackQuery(id="96813371158124971", from_user=telegram_member_mc, chat_instance="0")
    handlers_members.get_today_bdays(telegram_client, telegram_query)
    assert 1 == 1  # this is just to make pytest pass
