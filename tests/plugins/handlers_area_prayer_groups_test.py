from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pyrogram import errors, raw
from pyrogram.types import CallbackQuery

from plugins import handlers_area_prayer_groups, handlers_main
from plugins.handlers_area_prayer_groups import build_message
from stoscbots.bot import keyboards
from stoscbots.util import bot_auth


@pytest.fixture(autouse=True)
def authorize_member(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)


def test_get_area_prayer_group_members_no_members():
    # Test case with empty member list
    member_list = []
    area_name = [["Test Area"]]
    result = build_message(member_list, area_name)
    assert result == "No members in this area"


def test_get_area_prayer_group_members_():
    # Test case with multiple members in the list
    member_list = [
        ["John Doe (1234)"],
        ["Jane Smith (5678)"]
    ]
    area_name = [["Test Area"]]
    result = build_message(member_list, area_name)
    expected_result = (
        "**Members in Test Area** `(2)`\n\n"
        "• John Doe `(1234)`\n"
        "• Jane Smith `(5678)`"
    )
    assert result == expected_result


@pytest.mark.asyncio
async def test_show_prayer_groups_menu_rich(monkeypatch):
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Prayer Groups Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    handler, _group = handlers_main.show_prayer_groups_menu.handlers[0]
    assert handler.filters(client, query)
    await handlers_main.show_prayer_groups_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    markup = client.send_rich_message.await_args.kwargs["reply_markup"]
    assert markup is keyboards.area_prayer_groups_keyboard
    blocks = (await rich.write(client=None)).blocks
    assert len(blocks) == 1
    assert "Area Prayer Groups" in blocks[0].text.texts[0].text.text
    callbacks = [[b.callback_data for b in row] for row in markup.inline_keyboard]
    assert callbacks == [
        ["Area Prayer Group 1", "Area Prayer Group 2"],
        ["Area Prayer Group 3", "Area Prayer Group 4"],
        ["Area Prayer Group 5", "Area Prayer Group 6"],
        ["Area Prayer Group 7", "Main Menu"],
    ]
    client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_show_prayer_groups_menu_fallback(monkeypatch):
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Prayer Groups Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_prayer_groups_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert text == "Area Prayer Groups"
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.area_prayer_groups_keyboard


@pytest.mark.asyncio
@pytest.mark.parametrize("rich_supported", [True, False])
async def test_get_area_prayer_group_members(monkeypatch, rich_supported):
    members = [
        ("Alex Morgan (A001)",),
        ("Jamie Lee (J022)",),
        ("Other Member",),
    ]
    monkeypatch.setattr(handlers_area_prayer_groups.db, "get_members_for_area", lambda area: (members, [["East Coast"]]))

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=None if rich_supported else errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Area Prayer Group 1")
    monkeypatch.setattr(query, "answer", AsyncMock())

    handler, _group = handlers_area_prayer_groups.get_area_prayer_group_members.handlers[0]
    assert handler.filters(client, query)
    await handlers_area_prayer_groups.get_area_prayer_group_members.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.back_to_prayer_groups_keyboard

    if not rich_supported:
        client.send_message.assert_awaited_once()
        _, text = client.send_message.await_args.args
        assert "Members in East Coast" in text and "(3)" in text
        assert "Alex Morgan" in text
        return

    client.send_message.assert_not_awaited()
    blocks = (await rich.write(client=None)).blocks
    heading, subtitle, table, footer = blocks
    assert heading.text.text == "East Coast 🤲🏻"
    assert subtitle.text.text == "3 families"
    assert isinstance(table, raw.types.PageBlockTable) and table.striped and table.compact
    assert [cell.text.text for cell in table.rows[0].cells] == ["Family"]

    # First row has tappable A001
    first_cell_texts = table.rows[1].cells[0].text.texts
    assert first_cell_texts[0].text == "Alex Morgan"
    assert first_cell_texts[2].type.data == b"related_family:A001"

    # Second row has tappable J022
    second_cell_texts = table.rows[2].cells[0].text.texts
    assert second_cell_texts[0].text == "Jamie Lee"
    assert second_cell_texts[2].type.data == b"related_family:J022"

    # Third row is plain text
    assert table.rows[3].cells[0].text.text == "Other Member"
    assert "Tap a family code" in footer.text.text


@pytest.mark.asyncio
async def test_get_area_prayer_group_members_empty(monkeypatch):
    monkeypatch.setattr(handlers_area_prayer_groups.db, "get_members_for_area", lambda area: ([], [["Woodlands"]]))

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Area Prayer Group 5")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_area_prayer_groups.get_area_prayer_group_members.__wrapped__(client, query)

    _, rich = client.send_rich_message.await_args.args
    blocks = (await rich.write(client=None)).blocks
    heading, empty_msg = blocks
    assert heading.text.text == "Woodlands 🤲🏻"
    assert empty_msg.text.text == "No members registered in this area."
