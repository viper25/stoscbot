from plugins import handlers_main
from stoscbots.util.utils import generate_profile_msg_for_family
from tests.mocks import *
import pytest
from types import SimpleNamespace
from stoscbots.util import bot_auth, utils


@pytest.mark.asyncio
async def test_start_handler(monkeypatch):
    async def fake_send_message(*_args, **_kwargs):
        return None

    async def fake_send_sticker(*_args, **_kwargs):
        return None

    async def fake_reply_text(*_args, **_kwargs):
        return None

    monkeypatch.setattr(telegram_client, "send_message", fake_send_message, raising=False)
    monkeypatch.setattr(telegram_client, "send_sticker", fake_send_sticker, raising=False)
    monkeypatch.setattr(msg, "reply_text", fake_reply_text, raising=False)
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(bot_auth, "get_super_admin_id", lambda: "1234")

    msg.command = ["start"]
    msg.from_user = telegram_member_mc
    await handlers_main.start_handler(telegram_client, msg)
    assert 1 == 1


@pytest.mark.asyncio
async def test_start_handler_invalid_member(monkeypatch):
    async def fake_send_message(*_args, **_kwargs):
        return None

    async def fake_send_sticker(*_args, **_kwargs):
        return None

    async def fake_reply_text(*_args, **_kwargs):
        return None

    async def fake_reply(*_args, **_kwargs):
        return None

    responses = iter([SimpleNamespace(text="A001"), SimpleNamespace(text="user@example.com")])

    async def fake_listen_message(*_args, **_kwargs):
        return next(responses)

    async def fake_listen_cancel(*_args, **_kwargs):
        return None

    monkeypatch.setattr(telegram_client, "send_message", fake_send_message, raising=False)
    monkeypatch.setattr(telegram_client, "send_sticker", fake_send_sticker, raising=False)
    monkeypatch.setattr(telegram_client, "listen",
                        SimpleNamespace(Message=fake_listen_message, Cancel=fake_listen_cancel),
                        raising=False)
    monkeypatch.setattr(msg, "reply_text", fake_reply_text, raising=False)
    monkeypatch.setattr(msg, "reply", fake_reply, raising=False)
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: False)
    monkeypatch.setattr(bot_auth, "get_super_admin_id", lambda: "1234")
    monkeypatch.setattr(utils, "is_valid_member_code", lambda _text: True)
    monkeypatch.setattr(utils, "is_valid_email", lambda _text: True)

    msg.command = ["start"]
    msg.from_user = telegram_member_non
    await handlers_main.start_handler(telegram_client, msg)
    assert 1 == 1
