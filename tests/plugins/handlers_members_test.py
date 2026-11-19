from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pyrogram import errors, raw
from pyrogram.types import CallbackQuery, RichMessage

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


@pytest.mark.asyncio
@pytest.mark.parametrize(("handler", "lookup", "result", "heading", "body_contains", "codes"), [
    (handlers_members.get_weeks_bdays, "get_bday", ("Nov 16", "Nov 22", [
        ("A123", "Alex Example", "19/11", None),
    ]), "Birthdays this week 🎂", "Nov 16 – Nov 22\n• Alex Example (A123) - NA", ["A123"]),
    (handlers_members.get_weeks_anniversaries, "get_anniversaries", ("Nov 16", "Nov 22", [
        ("B456", "Jamie & Casey Example", date(1900, 11, 19)),
    ]), "Wedding anniversaries this week 💍", "Jamie & Casey Example (B456) - NA", ["B456"]),
    (handlers_members.get_new_members, "get_new_members", [
        ("New Example (C789)",), ("Family without a code",),
    ], "New members 🆕", "Last 12 months\n• New Example (C789)\n• Family without a code", ["C789"]),
    (handlers_members.get_MC, None, None, "Management committee", "Lay Steward:",
     ["J022", "V019", "M030", "G006", "S028", "S030", "O001", "D017"]),
    (handlers_members.member_gb_ineligible, "get_gb_eligible_count", [(99,)],
     "General Body & quorum", "Eligible members: 99\nQuorum (25%): 24", []),
])
async def test_members_result_cards(monkeypatch, handler, lookup, result, heading, body_contains, codes):
    if lookup:
        monkeypatch.setattr(handlers_members.db, lookup, lambda *args, **kwargs: result)
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42))
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handler.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is handlers_members.keyboards.back_to_members_keyboard
    title, body = (await rich.write(client=None)).blocks
    assert title.text.text.text == heading
    parts = body.text.texts
    assert body_contains in "".join(part.text.text if isinstance(part, raw.types.TextButton) else part.text for part in parts)
    assert [part.type.data for part in parts if isinstance(part, raw.types.TextButton)] == [
        f"related_family:{code}".encode() for code in codes
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(("handler", "lookup", "row"), [
    (handlers_members.get_weeks_bdays, "get_bday", ("A123", "Alex Example", "19/11/1980", None)),
    (handlers_members.get_weeks_anniversaries, "get_anniversaries",
     ("A123", "Alex Example", date(1980, 11, 19))),
])
async def test_weekly_commands_keep_text_output_without_years(monkeypatch, handler, lookup, row):
    monkeypatch.setattr(handlers_members.db, lookup, lambda _period: ("Nov 16", "Nov 22", [row]))
    client = SimpleNamespace(send_rich_message=AsyncMock())
    message = SimpleNamespace(reply_text=AsyncMock())

    await handler.__wrapped__(client, message)

    message.reply_text.assert_awaited_once()
    text = message.reply_text.await_args.args[0]
    assert "Alex Example" in text and "1980" not in text and "yrs" not in text
    client.send_rich_message.assert_not_awaited()
