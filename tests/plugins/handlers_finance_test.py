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
    assert "🔹 Received: $150.00" in repr(serialized.blocks[2].text)
    assert "🔸 Paid: $420.50" in repr(serialized.blocks[2].text)
    table_repr = repr(serialized.blocks[1])
    assert "🔹 Member John" in table_repr
    assert "🔸 SPS Services" in table_repr


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
    assert "🔹 **Member John**" in text
    assert "🔸 **SPS Services**" in text
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
    assert "🔹 Inflow: $200.00" in repr(serialized.blocks[2].text)
    assert "🔸 Outflow: $500.00" in repr(serialized.blocks[2].text)
    table_repr = repr(serialized.blocks[1])
    assert "🔹 Donor Alice" in table_repr
    assert "🔸 Transfer Out" in table_repr


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
    assert "🔹 **Donor Alice**" in text
    assert "🔸 **Transfer Out**" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard


@pytest.fixture
def mock_trial_balance_data():
    return {
        "Reports": [{
            "Rows": [
                {
                    "RowType": "Header",
                    "Cells": [
                        {"Value": "Account"},
                        {"Value": "Debit"},
                        {"Value": "Credit"},
                        {"Value": "YTD Debit"},
                        {"Value": "YTD Credit"},
                    ],
                },
                {
                    "RowType": "Section",
                    "Title": "Revenue",
                    "Rows": [
                        {
                            "RowType": "Row",
                            "Cells": [
                                {"Value": "General Subscription"},
                                {"Value": ""},
                                {"Value": "1000"},
                                {"Value": ""},
                                {"Value": "15000.00"},
                            ],
                        },
                        {
                            "RowType": "Row",
                            "Cells": [
                                {"Value": "Auction Proceeds"},
                                {"Value": ""},
                                {"Value": "500"},
                                {"Value": ""},
                                {"Value": "8500.00"},
                            ],
                        },
                        {
                            "RowType": "SummaryRow",
                            "Cells": [
                                {"Value": "Total Revenue"},
                                {"Value": ""},
                                {"Value": "1500"},
                                {"Value": ""},
                                {"Value": "23500.00"},
                            ],
                        },
                    ],
                },
                {
                    "RowType": "Section",
                    "Title": "Operating Expenses",
                    "Rows": [
                        {
                            "RowType": "Row",
                            "Cells": [
                                {"Value": "Cathedral Utilities"},
                                {"Value": "600"},
                                {"Value": ""},
                                {"Value": "4200.00"},
                                {"Value": ""},
                            ],
                        },
                        {
                            "RowType": "SummaryRow",
                            "Cells": [
                                {"Value": "Total Operating Expenses"},
                                {"Value": "600"},
                                {"Value": ""},
                                {"Value": "4200.00"},
                                {"Value": ""},
                            ],
                        },
                    ],
                },
            ]
        }]
    }


@pytest.mark.asyncio
async def test_get_finance_trial_balance_revenue_rich(monkeypatch, mock_trial_balance_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_trial_balance", lambda _paymentsOnly: mock_trial_balance_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Trial Balance Revenue Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_trial_balance.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header, Table, Footer
    assert "Trial Balance — Revenue" in repr(serialized.blocks[0].text)
    table_repr = repr(serialized.blocks[1])
    assert "General Subscription" in table_repr
    assert "15,000.00" in table_repr
    assert "Auction Proceeds" in table_repr
    assert "8,500.00" in table_repr
    footer_repr = repr(serialized.blocks[2].text)
    assert "🔹 Total Revenue: $23,500.00" in footer_repr


@pytest.mark.asyncio
async def test_get_finance_trial_balance_expense_rich(monkeypatch, mock_trial_balance_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_trial_balance", lambda _paymentsOnly: mock_trial_balance_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Trial Balance Expense Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_trial_balance.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    assert client.send_rich_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3  # Header, Table, Footer
    assert "Trial Balance — Expense" in repr(serialized.blocks[0].text)
    table_repr = repr(serialized.blocks[1])
    assert "Cathedral Utilities" in table_repr
    assert "4,200.00" in table_repr
    footer_repr = repr(serialized.blocks[2].text)
    assert "🔸 Total Expense: $4,200.00" in footer_repr


@pytest.mark.asyncio
async def test_get_finance_trial_balance_fallback(monkeypatch, mock_trial_balance_data):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_trial_balance", lambda _paymentsOnly: mock_trial_balance_data)

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Trial Balance Revenue Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_trial_balance.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "TRIAL BALANCE — REVENUE" in text
    assert "General Subscription" in text
    assert "🔹 **Total Revenue: $23,500.00**" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard


@pytest.mark.asyncio
async def test_get_finance_trial_balance_empty(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    empty_report = {
        "Reports": [{
            "Rows": [
                {"RowType": "Header", "Cells": []},
                {"RowType": "Section", "Title": "Revenue", "Rows": []},
            ]
        }]
    }
    monkeypatch.setattr(xero_utils, "xero_get_trial_balance", lambda _paymentsOnly: empty_report)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Trial Balance Revenue Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_trial_balance.__wrapped__(client, query)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 2
    assert "No revenue account entries" in repr(serialized.blocks[1].text)


@pytest.mark.asyncio
async def test_get_finance_trial_balance_error(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(xero_utils, "xero_get_trial_balance", lambda _paymentsOnly: (_ for _ in ()).throw(RuntimeError("API error")))

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="Finance Trial Balance Revenue Button")
    monkeypatch.setattr(query, "answer", AsyncMock())

    await handlers_finance.get_finance_trial_balance.__wrapped__(client, query)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "Unable to fetch Trial Balance" in text
    assert client.send_message.await_args.kwargs["reply_markup"] is keyboards.finance_menu_keyboard


@pytest.fixture
def mock_member_details_row():
    return [
        "John Doe", "Kaniamparambil", "John", "M", "A001",
        "john@example.com", "", "91234567", "1980-01-01", "A001",
        "Blk 123", "#04-56", "Bedok North", "",
    ]


@pytest.fixture
def mock_member_payments_data():
    return [
        {
            "Account": "General Subscription",
            "LineAmount": "1200.00",
            "modified_ts": "2026-06-15T10:00:00",
        },
        {
            "Account": "Harvest Festival",
            "LineAmount": "350.00",
            "modified_ts": "2026-08-20T12:00:00",
        },
    ]


@pytest.fixture
def mock_member_invoices_data():
    return {
        "Invoices": [
            {
                "Type": "ACCREC",
                "InvoiceNumber": "INV-26001",
                "Status": "PAID",
                "Total": 1200.00,
                "AmountDue": 0.00,
                "DateString": "2026-01-10",
                "LineItems": [{"Description": "Subscription 2026", "LineAmount": 1200.00}],
            },
            {
                "Type": "ACCREC",
                "InvoiceNumber": "HF-26012",
                "Status": "AUTHORISED",
                "Total": 150.00,
                "AmountDue": 150.00,
                "DateString": "2026-08-15",
                "LineItems": [{"Description": "Harvest Auction", "LineAmount": 150.00}],
            },
        ]
    }


@pytest.mark.asyncio
async def test_finance_search_member_invalid_cmd(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    message = SimpleNamespace(
        id=1, command=["x"], text="/x",
        chat=SimpleNamespace(id=42), from_user=SimpleNamespace(id=42),
        reply=AsyncMock(),
    )
    await handlers_finance.finance_search_member.__wrapped__(client, message)
    message.reply.assert_awaited_once()
    assert "Please enter a valid Member Code" in message.reply.await_args.args[0]


@pytest.mark.asyncio
async def test_finance_search_member_not_found(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(handlers_finance.db, "get_member_details", lambda _code, _mode: [])
    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    message = SimpleNamespace(
        id=1, command=["x", "Z999"], text="/x Z999",
        chat=SimpleNamespace(id=42), from_user=SimpleNamespace(id=42),
        reply=AsyncMock(),
    )
    await handlers_finance.finance_search_member.__wrapped__(client, message)
    message.reply.assert_awaited_once()
    assert "No such Member" in message.reply.await_args.args[0]


@pytest.mark.asyncio
async def test_finance_search_member_x_payments_rich(
    monkeypatch, mock_member_details_row, mock_member_payments_data,
):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(handlers_finance.db, "get_member_details", lambda _code, _mode: [mock_member_details_row])
    monkeypatch.setattr(handlers_finance.utils, "get_member_payments", lambda _code, _year: mock_member_payments_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    message = SimpleNamespace(
        id=1, command=["x", "A001"], text="/x A001",
        chat=SimpleNamespace(id=42), from_user=SimpleNamespace(id=42),
        reply=AsyncMock(),
    )

    await handlers_finance.finance_search_member.__wrapped__(client, message)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    markup = client.send_rich_message.await_args.kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].callback_data.startswith("search_xero_dues:A001:")
    assert markup.inline_keyboard[0][1].callback_data == "related_family:A001"

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 3
    assert "Member Contributions" in repr(serialized.blocks[0].text)
    table_repr = repr(serialized.blocks[1])
    assert "General Subscription" in table_repr
    assert "1,200.00" in table_repr
    assert "Harvest Festival" in table_repr
    footer_repr = repr(serialized.blocks[2].text)
    assert "🔹 Total Contributions: $1,550.00" in footer_repr


@pytest.mark.asyncio
async def test_finance_search_member_xs_invoices_rich(
    monkeypatch, mock_member_details_row, mock_member_invoices_data,
):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(handlers_finance.db, "get_member_details", lambda _code, _mode: [mock_member_details_row])
    monkeypatch.setattr(xero_utils, "get_Invoices", lambda _code: mock_member_invoices_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    message = SimpleNamespace(
        id=1, command=["xs", "A001"], text="/xs A001",
        chat=SimpleNamespace(id=42), from_user=SimpleNamespace(id=42),
        reply=AsyncMock(),
    )

    await handlers_finance.finance_search_member.__wrapped__(client, message)

    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    markup = client.send_rich_message.await_args.kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].callback_data.startswith("search_xero_payments:A001:")
    assert markup.inline_keyboard[0][1].callback_data == "related_family:A001"

    serialized = await rich.write(client=None)
    assert len(serialized.blocks) == 4  # Header, Due Table, Settled Drawer, Footer
    assert "Member Invoices & Dues" in repr(serialized.blocks[0].text)
    due_table_repr = repr(serialized.blocks[1])
    assert "HF-26012" in due_table_repr
    assert "150.00" in due_table_repr
    footer_repr = repr(serialized.blocks[3].text)
    assert "🔸 Total Due: $150.00" in footer_repr
    assert "🔹 Total Settled: $1,200.00" in footer_repr


@pytest.mark.asyncio
async def test_finance_search_member_fallback(
    monkeypatch, mock_member_details_row, mock_member_payments_data,
):
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(handlers_finance.db, "get_member_details", lambda _code, _mode: [mock_member_details_row])
    monkeypatch.setattr(handlers_finance.utils, "get_member_payments", lambda _code, _year: mock_member_payments_data)

    client = SimpleNamespace(
        send_rich_message=AsyncMock(side_effect=errors.RichMessageUnsupported()),
        send_message=AsyncMock(),
    )
    message = SimpleNamespace(
        id=1, command=["x", "A001"], text="/x A001",
        chat=SimpleNamespace(id=42), from_user=SimpleNamespace(id=42),
        reply=AsyncMock(),
    )

    await handlers_finance.finance_search_member.__wrapped__(client, message)

    client.send_message.assert_awaited_once()
    chat_id, text = client.send_message.await_args.args
    assert chat_id == 42
    assert "General Subscription" in text
    markup = client.send_message.await_args.kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].callback_data.startswith("search_xero_dues:A001:")


@pytest.mark.asyncio
async def test_finance_search_member_callback(
    monkeypatch, mock_member_details_row, mock_member_invoices_data,
):
    import re
    monkeypatch.setattr(bot_auth, "is_mgmt_member", lambda _id: True)
    monkeypatch.setattr(handlers_finance.db, "get_member_details", lambda _code, _mode: [mock_member_details_row])
    monkeypatch.setattr(xero_utils, "get_Invoices", lambda _code: mock_member_invoices_data)

    client = SimpleNamespace(send_rich_message=AsyncMock(), send_message=AsyncMock())
    query = CallbackQuery(id="tap", from_user=SimpleNamespace(id=42), data="search_xero_dues:A001:2026")
    monkeypatch.setattr(query, "answer", AsyncMock())
    query.matches = [re.search(r"^search_xero_(payments|dues):([A-Z0-9]+):([0-9]{4})$", query.data)]

    await handlers_finance.finance_search_member_callback.__wrapped__(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    chat_id, rich = client.send_rich_message.await_args.args
    assert chat_id == 42
    serialized = await rich.write(client=None)
    assert "Member Invoices & Dues" in repr(serialized.blocks[0].text)

