from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pyrogram import errors, raw
from pyrogram.types import CallbackQuery

from plugins import handlers_members
from stoscbots.util import bot_auth


@pytest.fixture(autouse=True)
def authorize_member(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)


@pytest.mark.asyncio
@pytest.mark.parametrize(("handler", "lookup", "empty_text"), [
    (handlers_members.get_today_bdays, "get_bday", "No birthdays today"),
    (handlers_members.get_today_anniversaries, "get_anniversaries", "No wedding anniversaries today"),
])
async def test_today_celebrations_empty(monkeypatch, handler, lookup, empty_text):
    monkeypatch.setattr(handlers_members.db, lookup, lambda _period: (None, None, []))
    client = SimpleNamespace(send_rich_message=AsyncMock())
    query = SimpleNamespace(answer=AsyncMock(), from_user=SimpleNamespace(id=42))

    await handler.__wrapped__(client, query)

    _, rich = client.send_rich_message.await_args.args
    heading, body = (await rich.write(client=None)).blocks
    assert isinstance(heading, raw.types.PageBlockHeading3)
    assert body.text.text == empty_text
    markup = client.send_rich_message.await_args.kwargs["reply_markup"]
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
            "• Alex & Robin Example (a123) · 53\n"
            "• Jamie & Casey Example (B456) · —\n"
            "• Sam & Taylor Example (C789) · 0"
        )
        headers = ["Couple", "Years"]
        missing_note = "The wedding year is not available."
    else:
        handler = handlers_members.get_today_bdays
        lookup = "get_bday"
        title = "Birthdays today 🎂"
        rows = [
            ("a123", "Alex Example", f"19/11/{date.today().year - 53}", None),
            ("B456", "Jamie Example", "19/11/0", None),
            ("C789", "Sam Example", "19/11", None),
        ]
        expected = (
            "• Alex Example (a123) · 53\n"
            "• Jamie Example (B456) · NA\n"
            "• Sam Example (C789) · NA"
        )
        headers = ["Member", "Age"]
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
        if anniversaries:
            expected += f"\n\n¹ {missing_note}"
        assert client.send_message.await_args.args == (42, f"{title}\n\n{expected}")
        return

    client.send_message.assert_not_awaited()
    encoded = await rich.write(client=None)
    encoded.write()
    if anniversaries:
        heading, anchor, table, note = encoded.blocks
    else:
        heading, table = encoded.blocks
    assert heading.text.text == title
    assert table.striped and table.compact
    assert [cell.text.text for cell in table.rows[0].cells] == headers
    first, second, third = [row.cells for row in table.rows[1:]]
    assert first[1].text.text == "53" and first[1].align_right
    if anniversaries:
        assert second[1].text.url == f"#{note.text.texts[0].name}"
        assert note.text.texts[0].text.text == f"¹ {missing_note}"
        assert note.text.texts[-1].url == f"#{anchor.name}"
    else:
        for row in (second, third):
            assert isinstance(row[1].text, raw.types.TextPlain)
            assert row[1].text.text == "NA"
    assert [row[0].text.texts[2].type.data for row in (first, second, third)] == [
        b"related_family:A123", b"related_family:B456", b"related_family:C789",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(("handler", "lookup", "result", "heading", "headers", "first_row", "codes"), [
    (handlers_members.get_weeks_bdays, "get_bday", ("Nov 16", "Nov 22", [
        ("A123", "Alex Example", "19/11", None),
    ]), "Birthdays this week 🎂", ["Date", "Member", "Age"], ["19 Nov\nToday", "Alex Example (A123)", "NA"], ["A123"]),
    (handlers_members.get_new_members, "get_new_members", [
        ("New Example (C789)",), ("Family without a code",),
    ], "New members 🆕", ["Family"], ["New Example (C789)"], ["C789"]),
    (handlers_members.get_MC, None, None, "Management committee", ["Role", "Member"], None,
     ["J022", "V019", "M030", "G006", "S028", "S030", "O001", "D017"]),
    (handlers_members.member_gb_ineligible, "get_gb_eligible_count", [(99,)],
     "General Body & quorum", ["Measure", "Count"], ["Eligible members", "99"], []),
])
async def test_members_result_cards(monkeypatch, handler, lookup, result, heading, headers, first_row, codes):
    class FixedDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 19)

    monkeypatch.setattr(handlers_members, "date", FixedDate)
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
    blocks = (await rich.write(client=None)).blocks
    assert blocks[0].text.text == heading
    table = next(block for block in blocks if isinstance(block, raw.types.PageBlockTable))
    assert table.striped and table.compact
    assert [cell.text.text for cell in table.rows[0].cells] == headers

    def text(node):
        if isinstance(node, raw.types.TextConcat):
            return "".join(text(part) for part in node.texts)
        if isinstance(node, raw.types.TextPlain):
            return node.text
        return text(node.text)

    rows = table.rows[1:]
    if first_row:
        assert [text(cell.text) for cell in rows[0].cells] == first_row
    if lookup == "get_bday":
        assert isinstance(rows[0].cells[0].text, raw.types.TextMarked)
        assert isinstance(rows[0].cells[2].text, raw.types.TextPlain)
    elif lookup == "get_new_members":
        assert text(rows[1].cells[0].text) == "Family without a code"
    elif lookup == "get_gb_eligible_count":
        assert [text(cell.text) for cell in rows[1].cells] == ["Quorum (25%)", "24"]
    buttons = [
        part for row in rows for cell in row.cells if isinstance(cell.text, raw.types.TextConcat)
        for part in cell.text.texts if isinstance(part, raw.types.TextButton)
    ]
    assert [part.type.data for part in buttons] == [
        f"related_family:{code}".encode() for code in codes
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("rich_supported", [True, False])
async def test_weekly_anniversary_table(monkeypatch, rich_supported):
    today = date(2026, 11, 19)
    monkeypatch.setattr(handlers_members, "date", SimpleNamespace(today=lambda: today))
    monkeypatch.setattr(handlers_members.db, "get_anniversaries", lambda _period: ("Nov 16", "Nov 22", [
        ("A123", "Alex & Robin Example", date(2014, 11, 19)),
        ("B456", "Jamie & Casey Example", date(1900, 11, 22)),
    ]))
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=None if rich_supported else errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42))
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_members.get_weeks_anniversaries.__wrapped__(client, query)

    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is handlers_members.keyboards.back_to_members_keyboard
    if not rich_supported:
        _, text = client.send_message.await_args.args
        assert "19 Nov (Today) · Alex & Robin Example (A123) · 12" in text
        assert "22 Nov · Jamie & Casey Example (B456) · —" in text
        assert "The wedding year is not available." in text
        return

    client.send_message.assert_not_awaited()
    encoded = await rich.write(client=None)
    encoded.write()
    heading, week, anchor, table, note = encoded.blocks
    assert isinstance(heading, raw.types.PageBlockHeading3)
    assert week.text.text == "Nov 16 – Nov 22"
    assert isinstance(table, raw.types.PageBlockTable) and table.striped and table.compact
    assert [cell.text.text for cell in table.rows[0].cells] == ["Date", "Couple", "Years"]
    first, second = [row.cells for row in table.rows[1:]]
    assert isinstance(first[0].text, raw.types.TextMarked)
    assert first[0].text.text.text == "19 Nov\nToday"
    assert first[1].text.texts[2].type.data == b"related_family:A123"
    assert first[2].text.text == "12"
    assert second[2].text.url == f"#{note.text.texts[0].name}"
    assert note.text.texts[-1].url == f"#{anchor.name}"


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
