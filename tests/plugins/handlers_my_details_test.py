from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pyrogram import errors, raw
from pyrogram.types import CallbackQuery

from plugins import handlers_main, handlers_my_details
from stoscbots.bot import family_profile, keyboards
from stoscbots.util import bot_auth, utils


@pytest.fixture(autouse=True)
def authorize_member(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_member", lambda _id: True)


@pytest.mark.asyncio
async def test_my_details_menu_rich(monkeypatch):
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Details Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    handler, _group = handlers_main.show_my_details_menu.handlers[0]
    assert handler.filters(client, query)
    await handlers_main.show_my_details_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    blocks = (await rich.write(client=None)).blocks
    header, profile_btn, financial_btns, drawer, main_menu = blocks

    assert header.text.texts[0].text.text == "My Details"
    assert profile_btn.buttons[0].type.data == b"My Profile"
    assert [b.type.data for b in financial_btns.buttons] == [b"My Contributions", b"My Dues"]
    assert drawer.title.text == "Church giving & services"
    assert drawer.blocks[0].buttons[0].type.data == b"List of Accounts"
    assert isinstance(drawer.blocks[1].buttons[0].type, raw.types.InlineButtonTypeWebView)
    assert main_menu.buttons[0].type.data == b"Main Menu"
    client.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_my_details_menu_fallback(monkeypatch):
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Details Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_my_details_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert text == "My Details"
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.my_details_menu_keyboard


@pytest.mark.asyncio
async def test_show_my_profile(monkeypatch):
    monkeypatch.setattr(utils, "getMemberCode_from_TelegramID", lambda _id: "V019")
    family_row = (123, "V019", "Vibin Kuriakose")
    monkeypatch.setattr(handlers_my_details.db, "get_member_details", lambda code, mode: [family_row])
    send_card = AsyncMock()
    monkeypatch.setattr(family_profile, "send_family_profile", send_card)

    client = SimpleNamespace()
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Profile")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_my_details.show_my_profile.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    send_card.assert_awaited_once_with(
        client, 42, family_row,
        reply_markup=keyboards.back_to_my_details_keyboard,
        note="Please contact the church office or secretary@stscoc.com to update any details.",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("rich_supported", [True, False])
async def test_show_my_contributions_with_payments(monkeypatch, rich_supported):
    monkeypatch.setattr(utils, "getMemberCode_from_TelegramID", lambda _id: "V019")
    monkeypatch.setattr(
        handlers_my_details.db, "get_member_details",
        lambda code, mode: [(1, "V019", "Vibin Kuriakose")],
    )
    payments = [
        {"Account": "Monthly Subscription", "LineAmount": "300.00", "modified_ts": "2026-11-01 10:30:00"},
        {"Account": "Harvest Festival", "LineAmount": "150.00", "modified_ts": "2026-11-15 14:00:00"},
    ]
    monkeypatch.setattr(utils, "get_member_payments", lambda code, year: payments)

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=None if rich_supported else errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Contributions")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_my_details.show_my_contributions.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.back_to_my_details_keyboard

    if not rich_supported:
        client.send_message.assert_awaited_once()
        _, text = client.send_message.await_args.args
        assert "Monthly Subscription: **$300.00**" in text
        assert "Harvest Festival: **$150.00**" in text
        return

    client.send_message.assert_not_awaited()
    blocks = (await rich.write(client=None)).blocks
    heading, subtitle, table, footer = blocks
    assert "Contributions" in heading.text.text
    assert "Vibin Kuriakose (V019)" in subtitle.text.text
    assert isinstance(table, raw.types.PageBlockTable) and table.striped and table.compact
    assert [cell.text.text for cell in table.rows[0].cells] == ["Account", "Amount ($)"]
    assert table.rows[1].cells[0].text.text == "Monthly Subscription"
    assert table.rows[1].cells[1].text.text == "300.00"
    assert table.rows[2].cells[0].text.text == "Harvest Festival"
    assert table.rows[2].cells[1].text.text == "150.00"
    assert "Total: $450.00" in footer.text.text
    assert "2026-11-15 14:00" in footer.text.text


@pytest.mark.asyncio
async def test_show_my_contributions_empty(monkeypatch):
    monkeypatch.setattr(utils, "getMemberCode_from_TelegramID", lambda _id: "V019")
    monkeypatch.setattr(handlers_my_details.db, "get_member_details", lambda code, mode: [(1, "V019", "Vibin")])
    monkeypatch.setattr(utils, "get_member_payments", lambda code, year: [])

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Contributions")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_my_details.show_my_contributions.__wrapped__(client, query)

    _, rich = client.send_rich_message.await_args.args
    blocks = (await rich.write(client=None)).blocks
    heading, subtitle, empty_msg = blocks
    assert "Contributions" in heading.text.text
    assert "No contributions recorded" in empty_msg.text.text


@pytest.mark.asyncio
@pytest.mark.parametrize("has_dues", [True, False])
async def test_show_my_subscriptions(monkeypatch, has_dues):
    current_year = str(datetime.now().year)
    monkeypatch.setattr(utils, "getMemberCode_from_TelegramID", lambda _id: "V019")
    invoices = {
        "Invoices": [
            {
                "Type": "ACCREC",
                "InvoiceNumber": f"INV-{current_year[2:]}01",
                "AmountDue": 250.0 if has_dues else 0.0,
                "Total": 250.0,
                "Status": "AUTHORISED" if has_dues else "PAID",
                "DateString": f"{current_year}-01-15",
                "LineItems": [{"Description": "Subscription 2026", "LineAmount": 250.0}],
            }
        ]
    }
    monkeypatch.setattr(handlers_my_details.xero_utils, "get_Invoices", lambda code: invoices)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="My Dues")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_my_details.show_my_subscriptions.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    markup = client.send_rich_message.await_args.kwargs["reply_markup"]

    blocks = (await rich.write(client=None)).blocks
    if has_dues:
        assert markup is keyboards.dues_payment_keyboard
        heading, subtitle, table, footer = blocks
        assert heading.text.text == "Outstanding Dues 📜"
        assert f"Family code: V019 · {current_year}" in subtitle.text.text
        assert [cell.text.text for cell in table.rows[0].cells] == ["Invoice", "Description", "Due ($)"]
        assert table.rows[1].cells[0].text.text == f"INV-{current_year[2:]}01"
        assert table.rows[1].cells[1].text.text == "Subscription 2026"
        assert table.rows[1].cells[2].text.text == "250.00"
        assert footer.text.text == "Total Due: $250.00"
    else:
        assert markup is keyboards.back_to_my_details_keyboard
        heading, subtitle, status_msg = blocks
        assert "All subscriptions and dues are up to date! 🟢" in status_msg.text.text


@pytest.mark.asyncio
async def test_show_list_accounts(monkeypatch):
    current_year = str(datetime.now().year)
    monkeypatch.setattr(utils, "getMemberCode_from_TelegramID", lambda _id: "V019")
    monkeypatch.setattr(
        handlers_my_details, "LIST_ACCOUNTS",
        [{"Code": "3100", "Name": "Monthly Subscription"}, {"Code": "3200", "Name": "Building Fund"}],
    )
    payments = [{"AccountCode": f"{current_year}_3100", "LineAmount": "120.00"}]
    monkeypatch.setattr(utils, "get_member_payments", lambda code, year: payments)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="List of Accounts")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_my_details.show_list_accounts.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    _, rich = client.send_rich_message.await_args.args
    blocks = (await rich.write(client=None)).blocks
    heading, subtitle, table, footer = blocks
    assert heading.text.text == "Church Accounts & Giving ℹ"
    assert [cell.text.text for cell in table.rows[0].cells] == ["Account", f"Contributed ({current_year})"]
    # 3100 is contributed, so bold
    assert isinstance(table.rows[1].cells[0].text, raw.types.TextBold)
    assert table.rows[1].cells[0].text.text.text == "Monthly Subscription"
    assert isinstance(table.rows[1].cells[1].text, raw.types.TextBold)
    assert table.rows[1].cells[1].text.text.text == "$120"
    # 3200 is not contributed, plain text and dash
    assert table.rows[2].cells[0].text.text == "Building Fund"
    assert table.rows[2].cells[1].text.text == "—"
    assert "Quote your family code" in footer.text.text
