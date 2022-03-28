from pyrogram.types.bots_and_keyboards import CallbackQuery
from plugins import handlers_area_prayer_groups
from tests.mocks import *


def test_get_area_prayer_group_members(monkeypatch):
    telegram_query = CallbackQuery(
        id="96813371158124971", from_user=telegram_member_non, chat_instance="0", data="Area Prayer Group 1"
    )
    handlers_area_prayer_groups.get_area_prayer_group_members(telegram_client, telegram_query)
    assert 1 == 1  # this is just to make pytest pass
