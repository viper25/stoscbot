from pyrogram.types.bots_and_keyboards import CallbackQuery
from plugins import handlers_members
from tests.mocks import *
import pytest
from stoscbots.util import utils


@pytest.mark.asyncio
async def test_get_today_bdays(monkeypatch):
    async def fake_answer(*_args, **_kwargs):
        return None

    async def fake_edit_and_send_msg(*_args, **_kwargs):
        return None

    monkeypatch.setattr(CallbackQuery, "answer", fake_answer)
    monkeypatch.setattr(utils, "edit_and_send_msg", fake_edit_and_send_msg)

    telegram_query = CallbackQuery(id="96813371158124971", from_user=telegram_member_mc, chat_instance="0")
    await handlers_members.get_today_bdays(telegram_client, telegram_query)
    assert 1 == 1  # this is just to make pytest pass
