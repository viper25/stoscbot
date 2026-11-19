from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pyrogram import errors, raw
from pyrogram.types import RichMessage

from plugins import handlers_members
from stoscbots.util import bot_auth


@pytest.fixture(autouse=True)
def authorize_member(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)


@pytest.mark.asyncio
async def test_get_today_bdays(monkeypatch):
    monkeypatch.setattr(handlers_members.db, "get_bday", lambda _period: (None, None, []))
    message = SimpleNamespace(rich_message=RichMessage(blocks=[]), reply_text=AsyncMock(), edit_text=AsyncMock())
    query = SimpleNamespace(answer=AsyncMock(), message=message, from_user=SimpleNamespace(id=42))

    await handlers_members.get_today_bdays.__wrapped__(None, query)

    message.reply_text.assert_awaited_once()
    message.edit_text.assert_not_awaited()
    assert message.reply_text.await_args.args == ("No Birthdays today",)
    markup = message.reply_text.await_args.kwargs["reply_markup"]
    assert [[button.callback_data for button in row] for row in markup.inline_keyboard] == [["Members Menu"]]


@pytest.mark.asyncio
@pytest.mark.parametrize("rich_supported", [True, False])
async def test_birthdays_today_lists_members_with_family_links(monkeypatch, rich_supported):
    rows = [
        ("a123", "Alex Example", f"19/11/{date.today().year - 53}", None),
        ("B456", "Jamie Example", "19/11/0", None),
        ("C789", "Sam Example", "19/11", None),
    ]
    monkeypatch.setattr(handlers_members.db, "get_bday", lambda _period: (None, None, rows))
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=None if rich_supported else errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = SimpleNamespace(answer=AsyncMock(), from_user=SimpleNamespace(id=42))

    await handlers_members.get_today_bdays.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is handlers_members.keyboards.back_to_members_keyboard
    if not rich_supported:
        client.send_message.assert_awaited_once()
        assert client.send_message.await_args.args == (
            42, "Birthdays today 🎂\n\n• Alex Example (a123) - 53\n• Jamie Example (B456) - NA\n• Sam Example (C789) - NA",
        )
        return

    client.send_message.assert_not_awaited()
    heading, birthday_list = (await rich.write(client=None)).blocks
    assert heading.text.text.text == "Birthdays today 🎂"
    parts = birthday_list.text.texts
    assert "".join(part.text.text if isinstance(part, raw.types.TextButton) else part.text for part in parts) == (
        "• Alex Example (a123) - 53\n• Jamie Example (B456) - NA\n• Sam Example (C789) - NA"
    )
    assert [part.type.data for part in parts if isinstance(part, raw.types.TextButton)] == [
        b"related_family:A123", b"related_family:B456", b"related_family:C789",
    ]
