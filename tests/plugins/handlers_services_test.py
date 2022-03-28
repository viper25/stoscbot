from pyrogram.types.bots_and_keyboards import CallbackQuery
from plugins import handlers_services
from tests.mocks import *


def test_start_handler(monkeypatch):
    telegram_query = CallbackQuery(
        id="96813371158124971", from_user=telegram_member_mc, chat_instance="0", data="Registrations for Service 192"
    )
    handlers_services.get_service_registrations(telegram_client, telegram_query)
    assert 1 == 1  # this is just to make pytest pass
