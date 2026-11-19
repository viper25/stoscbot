from datetime import UTC, date, datetime
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pyrogram import enums, errors, raw
from pyrogram.types import CallbackQuery

from plugins import handlers_main
from stoscbots.bot import family_profile
from stoscbots.util import bot_auth, utils
from stoscbots.util.utils import generate_profile_msg_for_family
from tests.mocks import *


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
