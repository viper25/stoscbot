import platform
import subprocess
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pyrogram import errors
from pyrogram.types import CallbackQuery

from plugins import handlers_streaming
from stoscbots.bot import keyboards
from stoscbots.util import bot_auth


@pytest.mark.asyncio
async def test_generate_announcement_slides_linux_rich(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    mock_run = SimpleNamespace(returncode=0, stdout="Slides built", stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_run)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Generate Announcement Slides")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_streaming.generate_announcement_slides.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.streaming_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 2
    assert "Announcement Slides Generation ✅" in repr(serialized.blocks[0].text)


@pytest.mark.asyncio
async def test_generate_announcement_slides_non_linux_rich(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Generate Announcement Slides")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_streaming.generate_announcement_slides.__wrapped__(client, query)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    serialized = await rich.write(client=None)
    assert "Slide Generator Unavailable ⚠️" in repr(serialized.blocks[0].text)


@pytest.mark.asyncio
async def test_generate_announcement_slides_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    mock_run = SimpleNamespace(returncode=0, stdout="OK", stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: mock_run)

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Generate Announcement Slides")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_streaming.generate_announcement_slides.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "Started slides generation" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.streaming_menu_keyboard
