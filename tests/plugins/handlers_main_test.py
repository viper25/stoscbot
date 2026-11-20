import os
from datetime import UTC, date, datetime
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pyrogram import enums, errors, raw
from pyrogram.types import CallbackQuery

from plugins import handlers_main
from stoscbots.bot import family_profile, keyboards
from stoscbots.util import bot_auth, utils
from tests.mocks import msg, telegram_client, telegram_member_non


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["member", "committee", "admin"])
async def test_start_handler(monkeypatch, role):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: role == "committee")
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda _id: role == "admin")
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    message = SimpleNamespace(command=["start"], from_user=SimpleNamespace(id=42))
    await handlers_main.start_handler.__wrapped__(client, message)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert not client.send_rich_message.await_args.kwargs
    blocks = (await rich.write(client=None)).blocks

    def callbacks(button_blocks):
        return [button.type.data for b in button_blocks for button in b.buttons]

    # Block 0: Header
    header = blocks[0]
    assert "St. Thomas Orthodox Syrian Cathedral" in header.text.texts[0].text.text
    assert isinstance(blocks[1], raw.types.PageBlockDivider)

    # Block 2 & 3: Personal & Giving
    assert blocks[2].text.text.text == "👤 Personal & Giving"
    assert callbacks([blocks[3]]) == [b"My Details Menu", b"PayNow Menu"]
    assert blocks[3].buttons[0].style is None
    assert isinstance(blocks[4], raw.types.PageBlockDivider)

    # Block 5 & 6: Parish Community
    assert blocks[5].text.text.text == "👥 Parish Community"
    assert callbacks([blocks[6]]) == [b"Members Menu", b"Prayer Groups Menu", b"My Harvest Festival Menu"]

    if role == "member":
        assert isinstance(blocks[7], raw.types.PageBlockDivider)
        church_links = blocks[8]
        commands_doc = blocks[9]
        assert len(commands_doc.blocks) == 2
        assert isinstance(commands_doc.blocks[1], raw.types.PageBlockTable)
        assert commands_doc.blocks[1].striped and commands_doc.blocks[1].compact
        assert len(commands_doc.blocks[1].rows) == 7
    elif role == "committee":
        assert isinstance(blocks[7], raw.types.PageBlockDivider)
        assert blocks[8].text.text.text == "🏛️ Committee & Ministry"
        assert callbacks([blocks[9]]) == [b"Finance Menu", b"Streaming Menu"]
        assert isinstance(blocks[10], raw.types.PageBlockDivider)
        church_links = blocks[11]
        commands_doc = blocks[12]
        assert len(commands_doc.blocks) == 4
        assert isinstance(commands_doc.blocks[1], raw.types.PageBlockTable)
        assert isinstance(commands_doc.blocks[3], raw.types.PageBlockTable)
        assert len(commands_doc.blocks[3].rows) == 7
        assert commands_doc.blocks[3].rows[1].cells[0].text.text.text == "/x <code> [year]"
        assert commands_doc.blocks[3].rows[2].cells[0].text.text.text == "/xs <code> [year]"
    else:  # admin
        assert isinstance(blocks[7], raw.types.PageBlockDivider)
        assert blocks[8].text.text.text == "🏛️ Committee & Ministry"
        assert callbacks([blocks[9]]) == [b"Finance Menu", b"Streaming Menu"]
        assert isinstance(blocks[10], raw.types.PageBlockDivider)
        church_links = blocks[11]
        commands_doc = blocks[12]
        assert len(commands_doc.blocks) == 7
        assert isinstance(commands_doc.blocks[1], raw.types.PageBlockTable)
        assert isinstance(commands_doc.blocks[3], raw.types.PageBlockTable)
        assert callbacks([commands_doc.blocks[5]]) == [b"Admin Menu"]
        assert isinstance(commands_doc.blocks[6], raw.types.PageBlockTable)
        assert len(commands_doc.blocks[6].rows) == 5

    assert [(button.text.text, button.type.url) for button in church_links.buttons] == [
        ("🌐 Website", "https://stosc.com/"),
        ("📅 Calendar", "https://stosc.com/calendar/"),
        ("📺 Livestream", "https://stosc.com/live/"),
        ("🙏 Prayer Requests", "https://stosc.com/pr"),
    ]
    assert commands_doc.title.text == "📖 Commands & Documentation"
    assert not commands_doc.open
    client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_return_home_falls_back_to_inline_keyboard(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: False)
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda _id: False)
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = SimpleNamespace(answer=AsyncMock(), from_user=SimpleNamespace(id=42))
    await handlers_main.show_main_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    client.send_message.assert_awaited_once()
    assert client.send_message.await_args.args[0] == 42
    keyboard = client.send_message.await_args.kwargs["reply_markup"]
    assert {button.callback_data for row in keyboard.inline_keyboard for button in row} == {
        "My Details Menu", "Members Menu", "PayNow Menu", "Prayer Groups Menu", "My Harvest Festival Menu",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("rich_supported", [True, False])
async def test_members_submenu_today_first(monkeypatch, rich_supported):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=None if rich_supported else errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = SimpleNamespace(answer=AsyncMock(), from_user=SimpleNamespace(id=42))
    await handlers_main.show_members_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    if not rich_supported:
        client.send_message.assert_awaited_once_with(
            42, "Members", reply_markup=handlers_main.keyboards.members_menu_keyboard,
        )
        return

    client.send_message.assert_not_awaited()
    _, _, today, week, parish, home = (await rich.write(client=None)).blocks

    def callbacks(rows):
        return [button.type.data for row in rows for button in row.buttons]

    assert callbacks([today]) == [b"Member Birthday Today Button", b"Member Anniversary Today Button"]
    assert week.title.text == "This week" and not week.open
    assert callbacks(week.blocks) == [b"Member Birthday Week Button", b"Member Anniversary Week Button"]
    assert parish.title.text == "Church & membership" and not parish.open
    assert callbacks(parish.blocks) == [b"New Members Button", b"MC", b"GB"]
    assert parish.blocks[-1].buttons[-1].text.text == "General Body & quorum"
    assert callbacks([home]) == [b"Main Menu"]


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


@pytest.fixture
def family_row():
    return (
        123, "A123", "Alex <Morgan>", "alex@example.com", "Alex <Morgan>", "alex@example.com",
        "Jamie Morgan", "jamie@example.com", "Taylor Morgan", "Casey Morgan", "12 Example Lane", None,
        "123456", "9123 4567", None, None, date(2008, 4, 5), "j073 / B245 (see notes)", "true", "North District",
        "1984-03-12", "1986-09-08", None, None, "2012-06-14",
    )


@pytest.mark.asyncio
async def test_member_code_returns_rich_family_profile(monkeypatch, family_row):
    lookups = []

    def get_member(code, search_type):
        lookups.append((code, search_type))
        return [family_row]

    monkeypatch.setattr(handlers_main.db, "get_member_details", get_member)
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(family_profile, "_family_photo", lambda _id: None)
    monkeypatch.setattr(utils, "get_address_details", lambda _zip: ("1.3521", "103.8198"))
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock(), send_venue=AsyncMock())
    message = SimpleNamespace(command=["u", "a123"], from_user=SimpleNamespace(id=42), chat=SimpleNamespace(id=-100))
    # Bypass access logging, but exercise the membership check.
    await handlers_main.member_search_cmd_handler.__wrapped__(client, message)

    assert lookups == [("a123", "code")]
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    blocks = (await rich.write(client=None)).blocks
    header, household, contact, dates, membership = blocks
    assert isinstance(header, raw.types.PageBlockParagraph)
    assert header.text.texts[0].text.text == "Alex <Morgan> & Jamie Morgan"
    assert header.text.texts[1].text == "\nFamily profile (A123)"
    assert isinstance(household, raw.types.PageBlockParagraph)
    assert household.text.texts[0].text.text == "Household"
    rows = household.text.texts[1:]
    assert [
        (linebreak.text, label.text.text, value.text)
        for linebreak, label, value in zip(rows[::3], rows[1::3], rows[2::3], strict=True)
    ] == [
        ("\n", "Head: ", "Alex <Morgan>"),
        ("\n", "Spouse: ", "Jamie Morgan"),
        ("\n", "Children: ", "Taylor Morgan"),
        ("\n", "Other family members: ", "Casey Morgan"),
    ]
    assert [block.title.text for block in (contact, dates, membership)] == [
        "Contact & address", "Birthdays & anniversary", "Membership & prayer group",
    ]
    assert all(not block.open for block in (contact, dates, membership))
    assert contact.blocks[1].text.texts[1].url == "https://wa.me/6591234567"
    assert isinstance(contact.blocks[-1], raw.types.InputPageBlockMap)
    for block, expected_text, expected_date in [
        (dates.blocks[0], "Mar 12, 1984", datetime(1984, 3, 12, tzinfo=UTC)),
        (dates.blocks[1], "Sep 8, 1986", datetime(1986, 9, 8, tzinfo=UTC)),
        (dates.blocks[2], "Jun 14, 2012", datetime(2012, 6, 14, tzinfo=UTC)),
        (membership.blocks[2], "Apr 5, 2008", datetime(2008, 4, 5, tzinfo=UTC)),
    ]:
        entity = block.text.texts[1]
        assert isinstance(entity, raw.types.TextDate)
        assert entity.text.text == expected_text
        assert entity.date == expected_date.timestamp()
    assert membership.blocks[1].text.texts[1].text == "On the roll"
    first, separator, second, note = membership.blocks[-1].text.texts[1].texts
    assert (first.text.text, second.text.text) == ("j073", "B245")
    assert first.type.data == b"related_family:J073"
    assert second.type.data == b"related_family:B245"
    assert first.style.link and second.style.link
    assert (separator.text, note.text) == (" / ", " (see notes)")
    client.send_venue.assert_not_called()
    client.send_message.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("authorized, found", [(True, True), (True, False), (False, True)])
async def test_related_family_tap(monkeypatch, family_row, authorized, found):
    callback_handler = handlers_main.related_family_handler
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="related_family:J073")
    answer = AsyncMock()
    monkeypatch.setattr(query, "answer", answer)
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: authorized)
    denied = AsyncMock()
    monkeypatch.setattr(bot_auth, "send_access_denied_msg", denied)
    lookup = Mock(return_value=[family_row] if found else [])
    monkeypatch.setattr(handlers_main.db, "get_member_details", lookup)
    send_card = AsyncMock()
    monkeypatch.setattr(family_profile, "send_family_profile", send_card)
    client = SimpleNamespace()

    handler, _group = callback_handler.handlers[0]
    assert await handler.filters(client, query)
    await callback_handler.__wrapped__(client, query)

    if not authorized:
        denied.assert_awaited_once_with(client, query)
        lookup.assert_not_called()
        send_card.assert_not_awaited()
    elif found:
        lookup.assert_called_once_with("J073", "code")
        answer.assert_awaited_once_with()
        send_card.assert_awaited_once_with(client, 42, family_row)
    else:
        lookup.assert_called_once_with("J073", "code")
        answer.assert_awaited_once_with("No such family: J073", show_alert=True)
        send_card.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejected_family_photo_retries_without_photo(monkeypatch, family_row):
    photo = BytesIO(b"test photo")
    monkeypatch.setattr(family_profile, "_family_photo", lambda _id: photo)
    monkeypatch.setattr(utils, "get_address_details", lambda _zip: None)
    layouts = []

    async def send_rich(_chat, rich):
        layouts.append([type(block).__name__ for block in rich.blocks])
        if len(layouts) == 1:
            raise errors.PhotoInvalidDimensions()

    client = SimpleNamespace(send_rich_message=send_rich, send_message=AsyncMock())
    await family_profile.send_family_profile(client, 42, family_row)

    assert layouts[0][:3] == ["InputRichBlockParagraph", "InputRichBlockPhoto", "InputRichBlockParagraph"]
    assert layouts[1] == layouts[0][:1] + layouts[0][2:]
    assert photo.closed
    client.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_unsupported_rich_family_profile_falls_back_to_text(monkeypatch, family_row):
    monkeypatch.setattr(family_profile, "_family_photo", lambda _id: None)
    monkeypatch.setattr(utils, "get_address_details", lambda _zip: None)
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    await family_profile.send_family_profile(client, 42, family_row)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "Alex <Morgan> & Jamie Morgan" in text
    assert "Household\nHead: Alex <Morgan>\nSpouse: Jamie Morgan\nChildren: Taylor Morgan" in text
    assert "Address: 12 Example Lane, 123456" in text
    assert "Head DOB: Mar 12, 1984" in text
    assert "Electoral roll: On the roll" in text
    assert "Related families: j073 / B245 (see notes)" in text
    assert client.send_message.await_args.kwargs["parse_mode"] == enums.ParseMode.DISABLED


@pytest.mark.asyncio
@pytest.mark.parametrize("spouse", [None, "Alex <Morgan>"])
async def test_household_shows_head_when_no_distinct_spouse(monkeypatch, family_row, spouse):
    row = list(family_row)
    row[6] = spouse
    row[8:10] = [None, None]
    monkeypatch.setattr(family_profile, "_family_photo", lambda _id: None)
    monkeypatch.setattr(utils, "get_address_details", lambda _zip: None)
    client = SimpleNamespace(send_rich_message=AsyncMock())

    await family_profile.send_family_profile(client, 42, tuple(row))

    _, rich = client.send_rich_message.await_args.args
    blocks = (await rich.write(client=None)).blocks
    heading, linebreak, label, value = blocks[1].text.texts
    assert heading.text.text == "Household"
    assert (linebreak.text, label.text.text, value.text) == ("\n", "Head: ", "Alex <Morgan>")
    assert isinstance(blocks[2], raw.types.PageBlockDetails)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, ""), ("1984-00-00", "1984-00-00"), ("1900-01-01", "Jan 1, 1900")],
)
def test_profile_dates_without_usable_timestamp_remain_text(value, expected):
    assert family_profile._date_field("Head DOB", value) == ("Head DOB", expected, None)


@pytest.mark.asyncio
async def test_show_paynow_menu_rich(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="PayNow Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    handler, _group = handlers_main.show_paynow_menu.handlers[0]
    assert handler.filters(client, query)
    await handlers_main.show_paynow_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.paynow_keyboard
    assert len(keyboards.paynow_keyboard.inline_keyboard) == 1
    assert keyboards.paynow_keyboard.inline_keyboard[0][0] is keyboards.BACK_TO_MAIN_BUTTON
    assert rich.blocks[1].photo.media == keyboards.PAYNOW_QR_MEDIA
    assert os.path.exists(keyboards.PAYNOW_QR_MEDIA)

    # Test the rich blocks when serialized (without photo to avoid un-mocked client upload)
    blocks = (await keyboards.get_rich_paynow_menu(include_photo=False).write(client=None)).blocks
    assert len(blocks) == 3
    header, methods, guide = blocks
    assert "Payment Options" in header.text.texts[0].text.text
    method_texts = [t.text.text for t in methods.text.texts if hasattr(t, "text") and hasattr(t.text, "text")]
    assert "S79SS0001L" in method_texts
    assert "0480155596" in method_texts
    assert guide.title.text == "Reference & receipt guide"
    client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_show_paynow_menu_photo_error_retries_without_photo(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    calls = []

    async def fake_send_rich(_chat, rich, **kwargs):
        calls.append(len(rich.blocks))
        if len(calls) == 1:
            raise errors.PhotoInvalid()

    client = SimpleNamespace(send_rich_message=fake_send_rich, send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="PayNow Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_paynow_menu.__wrapped__(client, query)

    assert len(calls) == 2
    # First call had 4 blocks (with photo), second call had 3 blocks (without photo)
    assert calls[0] == 4
    assert calls[1] == 3
    client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_show_paynow_menu_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="PayNow Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_paynow_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "S79SS0001L" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.paynow_keyboard


@pytest.mark.asyncio
async def test_show_my_harvest_festival_menu_rich_with_data(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(utils, "getMemberCode_from_TelegramID", lambda _id: "A001")
    monkeypatch.setattr(utils, "get_member_auction_purchases_data", lambda _c: {
        "items": [{"itemCode": "014", "itemName": "Spice Cake (2kg)", "winning_bid": 120, "bids": 5}],
        "total_bid": 120,
    })
    monkeypatch.setattr(utils, "get_member_auction_contributions_data", lambda _c: {
        "items": [{"itemCode": "008", "itemName": "Wooden Cross", "winner": "Mathew", "winning_bid": 150, "bids": 3}],
        "total_fetched": 150,
    })
    monkeypatch.setattr(utils, "get_member_auction_link", lambda _c: "https://harvest.stosc.com/?id=guid123")

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Harvest Festival Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    handler, _group = handlers_main.show_my_harvest_festival_menu.handlers[0]
    assert handler.filters(client, query)
    await handlers_main.show_my_harvest_festival_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.harvest_menu_keyboard
    assert len(keyboards.harvest_menu_keyboard.inline_keyboard) == 1
    assert keyboards.harvest_menu_keyboard.inline_keyboard[0][0].callback_data == "Main Menu"

    # Verify serialization of the rich message
    serialized = await rich.write(client=None)
    assert len(serialized.blocks) >= 4  # header, portal button, wins title, wins table, wins footer, donations drawer
    client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_show_my_harvest_festival_menu_empty(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(utils, "getMemberCode_from_TelegramID", lambda _id: "A002")
    monkeypatch.setattr(utils, "get_member_auction_purchases_data", lambda _c: None)
    monkeypatch.setattr(utils, "get_member_auction_contributions_data", lambda _c: None)
    monkeypatch.setattr(utils, "get_member_auction_link", lambda _c: "")

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Harvest Festival Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_my_harvest_festival_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42

    serialized = await rich.write(client=None)
    # Header + No bids paragraph
    assert len(serialized.blocks) == 2
    assert "No bids or purchases yet" in repr(serialized.blocks[1].text)
    client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_show_my_harvest_festival_menu_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(utils, "getMemberCode_from_TelegramID", lambda _id: "A001")
    monkeypatch.setattr(utils, "get_member_auction_purchases_data", lambda _c: None)
    monkeypatch.setattr(utils, "get_member_auction_contributions_data", lambda _c: None)
    monkeypatch.setattr(utils, "get_member_auction_link", lambda _c: "")
    monkeypatch.setattr(utils, "generate_msg_member_auction_purchases", lambda _c: "Purchases summary")
    monkeypatch.setattr(utils, "generate_msg_member_auction_contributions", lambda _c: "Donations summary")

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Harvest Festival Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_my_harvest_festival_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "Purchases summary" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.harvest_menu_keyboard


@pytest.mark.asyncio
async def test_show_streaming_menu_rich(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Streaming Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_streaming_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.streaming_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header, Guide Details, Buttons
    assert "Cathedral Media & Streaming" in repr(serialized.blocks[0].text)


@pytest.mark.asyncio
async def test_show_streaming_menu_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Streaming Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_streaming_menu.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "Streaming Menu" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.streaming_menu_keyboard


@pytest.fixture
def member_search_result_row():
    row = [None] * 26
    row[1] = "T001"
    row[2] = "Thomas Family"
    row[22] = 1  # Male
    row[23] = 1  # Head
    row[24] = "Thomas Mathew"
    row[25] = 101
    return row


@pytest.fixture
def person_row():
    return [
        "Thomas Mathew",        # 0: Name
        "Thomas Family",        # 1: fam_Name
        "Tom",                  # 2: Nickname
        "Software Engineer",    # 3: Profession
        1,                      # 4: per_Gender
        "thomas@example.com",   # 5: per_Email
        "family@example.com",   # 6: fam_Email
        "91234567",             # 7: CellPhone
        "1985-05-20",           # 8: DOB
        "T001",                 # 9: fam_Code
        "123 Orchard Rd",       # 10: Address1
        "#08-01",               # 11: Address2
        "238888",               # 12: Zip
        "A001, B002",           # 13: Related Families
        True,                   # 14: Electoral Roll
    ]


@pytest.mark.asyncio
async def test_member_search_free_text_rich(monkeypatch, member_search_result_row):
    child_row = list(member_search_result_row)
    child_row[23] = 3  # Child role
    child_row[24] = "Annika Mathew"
    child_row[25] = 102

    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(handlers_main.db, "get_member_details", lambda _q, _t: [member_search_result_row, child_row])

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    message = SimpleNamespace(
        command=["u", "Thomas"],
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=-100),
    )

    await handlers_main.member_search_cmd_handler.__wrapped__(client, message)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.back_to_main_keyboard
    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header, Table, Footer
    assert "Directory Search Results" in repr(serialized.blocks[0].text)
    table_repr = repr(serialized.blocks[1])
    assert "Thomas Mathew ⭐" in table_repr
    assert "Annika Mathew 🎒" in table_repr
    assert "T001" in table_repr
    assert "Member_T001_101" in table_repr
    assert "Member_T001_102" in table_repr
    assert "related_family:T001" in table_repr


@pytest.mark.asyncio
async def test_member_search_free_text_fallback(monkeypatch, member_search_result_row):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(handlers_main.db, "get_member_details", lambda _q, _t: [member_search_result_row])

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    message = SimpleNamespace(
        command=["u", "Thomas"],
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=-100),
        reply_text=AsyncMock(),
    )

    await handlers_main.member_search_cmd_handler.__wrapped__(client, message)

    message.reply_text.assert_awaited_once()
    text = message.reply_text.await_args.args[0]
    assert "Search results for `Thomas`" in text


@pytest.mark.asyncio
async def test_mobile_search_cmd_handler(monkeypatch, family_row):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(handlers_main.db, "get_member_details", lambda _q, _t: [family_row])
    send_card = AsyncMock()
    monkeypatch.setattr(family_profile, "send_family_profile", send_card)

    client = SimpleNamespace()
    message = SimpleNamespace(
        command=["t", "91234567"],
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=-100),
    )

    await handlers_main.mobile_search_cmd_handler.__wrapped__(client, message)

    send_card.assert_awaited_once_with(client, 42, family_row)


@pytest.mark.asyncio
async def test_mobile_search_cmd_handler_country_code_and_dedup(monkeypatch, family_row):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    queried = []

    def mock_get_member(query, search_type):
        queried.append((query, search_type))
        # Return duplicate rows to test deduplication
        return [family_row, family_row]

    monkeypatch.setattr(handlers_main.db, "get_member_details", mock_get_member)
    send_card = AsyncMock()
    monkeypatch.setattr(family_profile, "send_family_profile", send_card)

    client = SimpleNamespace()
    message = SimpleNamespace(
        command=["t", "+65 9123 4567"],
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=-100),
    )

    await handlers_main.mobile_search_cmd_handler.__wrapped__(client, message)

    assert queried == [("91234567", "mobile")]
    # Deduplication ensures send_family_profile is only called once per family
    send_card.assert_awaited_once_with(client, 42, family_row)


@pytest.mark.asyncio
async def test_mobile_search_cmd_handler_not_found(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(handlers_main.db, "get_member_details", lambda _q, _t: [])

    client = SimpleNamespace()
    message = SimpleNamespace(
        command=["t", "99999999"],
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=-100),
        reply_text=AsyncMock(),
    )

    await handlers_main.mobile_search_cmd_handler.__wrapped__(client, message)

    message.reply_text.assert_awaited_once()
    assert "No STOSC member found" in message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_mobile_search_cmd_handler_invalid_phone(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)

    client = SimpleNamespace()
    message = SimpleNamespace(
        command=["t", "12345"],
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=-100),
        reply_text=AsyncMock(),
    )

    await handlers_main.mobile_search_cmd_handler.__wrapped__(client, message)

    message.reply_text.assert_awaited_once()
    assert "Invalid Singapore Number" in message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_mobile_search_cmd_handler_missing_args(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)

    client = SimpleNamespace()
    message = SimpleNamespace(
        command=["t"],
        from_user=SimpleNamespace(id=42),
        chat=SimpleNamespace(id=-100),
        reply_text=AsyncMock(),
    )

    await handlers_main.mobile_search_cmd_handler.__wrapped__(client, message)

    message.reply_text.assert_awaited_once()
    assert "Please enter a Singapore Telephone" in message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_member_search_button_handler(monkeypatch, person_row):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(handlers_main.db, "get_member_details", lambda _id, _t: [person_row])
    send_person = AsyncMock()
    monkeypatch.setattr(family_profile, "send_person_profile", send_person)

    client = SimpleNamespace()
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Member_T001_101")
    query.answer = AsyncMock()

    await handlers_main.member_search_button_handler.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    send_person.assert_awaited_once_with(client, 42, person_row, "101")


@pytest.mark.asyncio
async def test_send_person_profile_rich(monkeypatch, person_row):
    monkeypatch.setattr(family_profile, "_person_photo", lambda _id: None)
    monkeypatch.setattr(utils, "get_address_details", lambda _zip: ("1.3521", "103.8198"))

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    await family_profile.send_person_profile(client, 42, person_row, 101)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    serialized = await rich.write(client=None)
    repr_str = repr(serialized.blocks)
    assert "Thomas Mathew" in repr_str
    assert "Software Engineer" in repr_str
    assert "thomas@example.com" in repr_str
    assert "91234567" in repr_str
    assert "123 Orchard Rd" in repr_str


@pytest.mark.asyncio
async def test_send_person_profile_photo_retry(monkeypatch, person_row):
    photo = BytesIO(b"person photo")
    monkeypatch.setattr(family_profile, "_person_photo", lambda _id: photo)
    monkeypatch.setattr(utils, "get_address_details", lambda _zip: None)

    layouts = []

    async def send_rich(chat_id, rich, **kwargs):
        layouts.append([type(block).__name__ for block in rich.blocks])
        if len(layouts) == 1:
            raise errors.PhotoInvalidDimensions()

    client = SimpleNamespace(send_rich_message=send_rich, send_message=AsyncMock())
    await family_profile.send_person_profile(client, 42, person_row, 101)

    assert layouts[0][:2] == ["InputRichBlockParagraph", "InputRichBlockPhoto"]
    assert layouts[1][1] != "InputRichBlockPhoto"
    assert photo.closed


@pytest.mark.asyncio
async def test_send_person_profile_fallback(monkeypatch, person_row):
    monkeypatch.setattr(family_profile, "_person_photo", lambda _id: None)
    monkeypatch.setattr(utils, "get_address_details", lambda _zip: None)
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )

    await family_profile.send_person_profile(client, 42, person_row, 101)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "Thomas Mathew" in text
    assert "Software Engineer" in text
    assert "91234567" in text


@pytest.fixture
def born_member_rows():
    return [
        ("Mathew Thomas", "2015-05-14", "Thomas Family (T001)", "thomas@example.com", "62886147", "91234567"),
        ("Sarah Alex", "2015-11-20", "Alex Family (A123)", "alex@example.com", None, "98765432"),
    ]


@pytest.mark.asyncio
async def test_members_born_year_missing_arg(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    client = SimpleNamespace()
    message = SimpleNamespace(
        command=["year"],
        from_user=SimpleNamespace(id=42, username="test", first_name="Test"),
        reply_text=AsyncMock(),
    )
    await handlers_main.members_born_after_year_handler.__wrapped__(client, message)
    message.reply_text.assert_awaited_once()
    assert "Please enter the year" in message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_members_born_year_invalid_year(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    client = SimpleNamespace()
    message = SimpleNamespace(
        command=["year", "abcd"],
        from_user=SimpleNamespace(id=42, username="test", first_name="Test"),
        reply_text=AsyncMock(),
    )
    await handlers_main.members_born_after_year_handler.__wrapped__(client, message)
    message.reply_text.assert_awaited_once()
    assert "valid 4-digit year" in message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_members_born_year_not_found(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(handlers_main.db, "get_members_born", lambda _y: [])
    client = SimpleNamespace()
    message = SimpleNamespace(
        command=["year", "1905"],
        from_user=SimpleNamespace(id=42, username="test", first_name="Test"),
        reply_text=AsyncMock(),
    )
    await handlers_main.members_born_after_year_handler.__wrapped__(client, message)
    message.reply_text.assert_awaited_once()
    assert "No members found born in 1905" in message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_members_born_year_rich(monkeypatch, born_member_rows):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(handlers_main.db, "get_members_born", lambda _y: born_member_rows)
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    message = SimpleNamespace(
        command=["year", "2015"],
        from_user=SimpleNamespace(id=42, username="test", first_name="Test"),
    )

    await handlers_main.members_born_after_year_handler.__wrapped__(client, message)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.back_to_main_keyboard
    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header, Table, Footer
    assert "Members Born in 2015" in repr(serialized.blocks[0].text)
    table_repr = repr(serialized.blocks[1])
    assert "Mathew Thomas" in table_repr
    assert "14 May" in table_repr
    assert "T001" in table_repr
    assert "related_family:T001" in table_repr
    assert "Sarah Alex" in table_repr
    assert "20 Nov" in table_repr
    assert "A123" in table_repr
    assert "related_family:A123" in table_repr


@pytest.mark.asyncio
async def test_members_born_year_fallback(monkeypatch, born_member_rows):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)
    monkeypatch.setattr(handlers_main.db, "get_members_born", lambda _y: born_member_rows)
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    message = SimpleNamespace(
        command=["year", "2015"],
        from_user=SimpleNamespace(id=42, username="test", first_name="Test"),
        reply_text=AsyncMock(),
    )

    await handlers_main.members_born_after_year_handler.__wrapped__(client, message)

    message.reply_text.assert_awaited_once()
    text = message.reply_text.await_args.args[0]
    assert "Members Born in 2015" in text
    assert "Mathew Thomas" in text
    assert "T001" in text
    assert message.reply_text.await_args.kwargs["reply_markup"] is keyboards.back_to_main_keyboard





