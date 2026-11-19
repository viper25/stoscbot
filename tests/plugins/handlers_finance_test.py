from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pyrogram import errors
from pyrogram.types import CallbackQuery

from plugins import handlers_finance, handlers_main
from stoscbots.bot import keyboards
from stoscbots.util import bot_auth
from stoscbots.xero import xero_utils


@pytest.fixture
def mock_bank_summary_data():
    return {
        "Reports": [{
            "Rows": [
                {
                    "RowType": "Header",
                    "Cells": [
                        {"Value": "Bank Account"},
                        {"Value": "Opening Balance"},
                        {"Value": "Received"},
                        {"Value": "Spent"},
                        {"Value": "Closing Balance"},
                    ]
                },
                {
                    "RowType": "Section",
                    "Rows": [
                        {
                            "Cells": [
                                {"Value": "DBS Operating"},
                                {"Value": "50000"},
                                {"Value": "10000"},
                                {"Value": "8000"},
                                {"Value": "52000.00"},
                            ]
                        },
                        {
                            "Cells": [
                                {"Value": "DBS FD 101"},
                                {"Value": "100000"},
                                {"Value": "0"},
                                {"Value": "0"},
                                {"Value": "100000.00"},
                            ]
                        },
                    ]
                }
            ]
        }]
    }


@pytest.fixture
def mock_executive_summary_data():
    return {
        "Reports": [{
            "Rows": [
                {
                    "RowType": "Header",
                    "Cells": [
                        {"Value": "Metric"},
                        {"Value": "Jan 2026"},
                        {"Value": "Dec 2025"},
                        {"Value": "Variance"},
                    ]
                },
                {
                    "RowType": "Section",
                    "Title": "Cash",
                    "Rows": [
                        {
                            "Cells": [
                                {"Value": "Cash received"},
                                {"Value": "52800"},
                                {"Value": "45200"},
                                {"Value": "16.8%"},
                            ]
                        },
                        {
                            "Cells": [
                                {"Value": "Cash spent"},
                                {"Value": "41000"},
                                {"Value": "38100"},
                                {"Value": "-7.6%"},
                            ]
                        },
                    ]
                },
                {
                    "RowType": "Section",
                    "Title": "Balance Sheet",
                    "Rows": [
                        {
                            "Cells": [
                                {"Value": "Operating surplus"},
                                {"Value": "11800"},
                                {"Value": "7100"},
                                {"Value": "66.2%"},
                            ]
                        }
                    ]
                }
            ]
        }]
    }


@pytest.mark.asyncio
async def test_show_finance_menu_rich(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    handler, _group = handlers_main.show_finance_menu.handlers[0]
    assert handler.filters(client, query)
    await handlers_main.show_finance_menu.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 1
    assert "Church Finance & Accounts" in repr(serialized.blocks[0].text)


@pytest.mark.asyncio
async def test_show_finance_menu_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Menu")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_main.show_finance_menu.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "Finance Menu" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard


@pytest.mark.asyncio
async def test_get_finance_bank_summary_rich(monkeypatch, mock_bank_summary_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "get_bank_summary", lambda: mock_bank_summary_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Bank Summary Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_bank_summary.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header, Table, Footer
    assert "Bank Accounts Summary" in repr(serialized.blocks[0].text)
    assert "100,000.00" in repr(serialized.blocks[2].text)


@pytest.mark.asyncio
async def test_get_finance_bank_summary_fallback(monkeypatch, mock_bank_summary_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "get_bank_summary", lambda: mock_bank_summary_data)

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Bank Summary Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_bank_summary.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "BANK ACCOUNTS SUMMARY" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard


@pytest.mark.asyncio
async def test_get_finance_executive_summary_rich(monkeypatch, mock_executive_summary_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "get_executive_summary", lambda: mock_executive_summary_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Executive Summary Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_executive_summary.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header + 2 section accordions (Cash, Profitability)
    assert "Financial Executive Summary" in repr(serialized.blocks[0].text)


@pytest.mark.asyncio
async def test_get_finance_executive_summary_fallback(monkeypatch, mock_executive_summary_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "get_executive_summary", lambda: mock_executive_summary_data)

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Executive Summary Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_executive_summary.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "EXECUTIVE SUMMARY" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard


@pytest.fixture
def mock_payments_data():
    return {
        "Payments": [
            {
                "Status": "AUTHORISED",
                "Date": "/Date(1672466400000+0000)/",
                "Amount": 150.00,
                "Invoice": {
                    "Type": "ACCREC",
                    "InvoiceNumber": "INV-1001",
                    "Contact": {"Name": "Member John"},
                },
            },
            {
                "Status": "AUTHORISED",
                "Date": "/Date(1672466400000+0000)/",
                "Amount": 420.50,
                "Invoice": {
                    "Type": "ACCPAY",
                    "InvoiceNumber": "BILL-2002",
                    "Contact": {"Name": "SPS Services"},
                },
            },
            {
                "Status": "DELETED",
                "Date": "/Date(1672466400000+0000)/",
                "Amount": 99.00,
                "Invoice": {
                    "Type": "ACCPAY",
                    "InvoiceNumber": "DEL-001",
                    "Contact": {"Name": "Ignore Me"},
                },
            },
        ]
    }


@pytest.fixture
def mock_bank_transactions_data():
    return {
        "BankTransactions": [
            {
                "Type": "RECEIVE",
                "Date": "/Date(1672466400000+0000)/",
                "Total": 200.00,
                "Contact": {"Name": "Donor Alice"},
                "BankAccount": {"Name": "DBS Operating"},
            },
            {
                "Type": "SPEND-TRANSFER",
                "Date": "/Date(1672466400000+0000)/",
                "Total": 500.00,
                "Contact": {"Name": "Transfer Out"},
                "BankAccount": {"Name": "CASH"},
            },
        ]
    }


@pytest.mark.asyncio
async def test_get_finance_payments_wtd_rich(monkeypatch, mock_payments_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_payments", lambda: mock_payments_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Payments WTD Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_payments_wtd_balance.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header, Table, Footer
    assert "Invoice & Bill Payments" in repr(serialized.blocks[0].text)
    assert "Received: $150.00" in repr(serialized.blocks[2].text)
    assert "Paid: $420.50" in repr(serialized.blocks[2].text)


@pytest.mark.asyncio
async def test_get_finance_payments_wtd_empty(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_payments", lambda: {"Payments": []})

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Payments WTD Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_payments_wtd_balance.__wrapped__(client, query)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 2
    assert "No invoice or bill payments" in repr(serialized.blocks[1].text)


@pytest.mark.asyncio
async def test_get_finance_payments_wtd_fallback(monkeypatch, mock_payments_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_payments", lambda: mock_payments_data)

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Payments WTD Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_payments_wtd_balance.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "INVOICE/BILL PAYMENTS" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard


@pytest.mark.asyncio
async def test_get_finance_latest_tx_rich(monkeypatch, mock_bank_transactions_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_bank_transactions", lambda: mock_bank_transactions_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Latest Transactions Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_latest_tx.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header, Table, Footer
    assert "Latest Transactions" in repr(serialized.blocks[0].text)
    assert "Inflow: $200.00" in repr(serialized.blocks[2].text)
    assert "Outflow: $500.00" in repr(serialized.blocks[2].text)


@pytest.mark.asyncio
async def test_get_finance_latest_tx_empty(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_bank_transactions", lambda: {"BankTransactions": []})

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Latest Transactions Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_latest_tx.__wrapped__(client, query)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 2
    assert "No non-invoice transactions" in repr(serialized.blocks[1].text)


@pytest.mark.asyncio
async def test_get_finance_latest_tx_fallback(monkeypatch, mock_bank_transactions_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_bank_transactions", lambda: mock_bank_transactions_data)

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Latest Transactions Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_latest_tx.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "TRANSACTIONS (WTD)" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard
