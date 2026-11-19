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
@pytest.mark.parametrize(("handler", "lookup", "empty_text"), [
    (handlers_members.get_today_bdays, "get_bday", "No Birthdays today"),
    (handlers_members.get_today_anniversaries, "get_anniversaries", "No Wedding Anniversary today"),
])
async def test_today_celebrations_empty(monkeypatch, handler, lookup, empty_text):
    monkeypatch.setattr(handlers_members.db, lookup, lambda _period: (None, None, []))
    message = SimpleNamespace(rich_message=RichMessage(blocks=[]), reply_text=AsyncMock(), edit_text=AsyncMock())
    query = SimpleNamespace(answer=AsyncMock(), message=message, from_user=SimpleNamespace(id=42))

    await handler.__wrapped__(None, query)

    message.reply_text.assert_awaited_once()
    message.edit_text.assert_not_awaited()
    assert message.reply_text.await_args.args == (empty_text,)
    markup = message.reply_text.await_args.kwargs["reply_markup"]
    assert [[button.callback_data for button in row] for row in markup.inline_keyboard] == [["Members Menu"]]


@pytest.mark.asyncio
@pytest.mark.parametrize("rich_supported", [True, False])
@pytest.mark.parametrize("anniversaries", [False, True])
async def test_today_celebrations_list_members_with_family_links(monkeypatch, rich_supported, anniversaries):
    if anniversaries:
        handler = handlers_members.get_today_anniversaries
        lookup = "get_anniversaries"
        title = "Wedding anniversaries today 💍"
        rows = [
            ("a123", "Alex & Robin Example", date(date.today().year - 53, 11, 19)),
            ("B456", "Jamie & Casey Example", date(1900, 11, 19)),
            ("C789", "Sam & Taylor Example", date(date.today().year, 11, 19)),
        ]
        expected = (
            "• Alex & Robin Example (a123) - 53\n"
            "• Jamie & Casey Example (B456) - NA\n"
            "• Sam & Taylor Example (C789) - NA"
        )
    else:
        handler = handlers_members.get_today_bdays
        lookup = "get_bday"
        title = "Birthdays today 🎂"
        rows = [
            ("a123", "Alex Example", f"19/11/{date.today().year - 53}", None),
            ("B456", "Jamie Example", "19/11/0", None),
            ("C789", "Sam Example", "19/11", None),
        ]
        expected = "• Alex Example (a123) - 53\n• Jamie Example (B456) - NA\n• Sam Example (C789) - NA"
    monkeypatch.setattr(handlers_members.db, lookup, lambda _period: (None, None, rows))
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=None if rich_supported else errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = SimpleNamespace(answer=AsyncMock(), from_user=SimpleNamespace(id=42))

    await handler.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is handlers_members.keyboards.back_to_members_keyboard
    if not rich_supported:
        client.send_message.assert_awaited_once()
        assert client.send_message.await_args.args == (42, f"{title}\n\n{expected}")
        return

    client.send_message.assert_not_awaited()
    heading, celebration_list = (await rich.write(client=None)).blocks
    assert heading.text.text.text == title
    parts = celebration_list.text.texts
    assert "".join(part.text.text if isinstance(part, raw.types.TextButton) else part.text for part in parts) == expected
    assert [part.type.data for part in parts if isinstance(part, raw.types.TextButton)] == [
        b"related_family:A123", b"related_family:B456", b"related_family:C789",
    ]
