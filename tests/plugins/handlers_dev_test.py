from plugins import handlers_dev
import pytest


def test_replace_ids_with_names_basic(monkeypatch):
    # Monkeypatch _id_to_name to a deterministic function
    monkeypatch.setattr(handlers_dev, "_id_to_name", lambda tid, cache: f"Name_{tid}")

    cmd_result = (
        "31 22541119\n"
        "18 727963517\n"
        "17 1619791510\n"
        "16 445003886\n"
        "15 1761265646\n"
        "15 1012921618\n"
        "10 56278607\n"
        "10 549367010\n"
        "8 8078279070\n"
        "7 1981928843\n"
        "6 1601643191\n"
        "5 913661281\n"
        "4 314887359\n"
        "2 6781143013\n"
        "1 5218624670\n"
        "not a match line"
    )

    out = handlers_dev._replace_ids_with_names(cmd_result)

    # Build expected by transforming each matching line, leaving others unchanged
    expected_lines = []
    for line in cmd_result.strip().splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            expected_lines.append(f"{parts[0]} Name_{parts[1]}")
        else:
            expected_lines.append(line)
    expected = "\n".join(expected_lines)

    assert out == expected


def test_id_to_name_uses_cache_and_handles_missing(monkeypatch):
    calls = {"count": 0}

    def mock_query_success(telegram_id: str):
        calls["count"] += 1
        return {"Items": [{"Name": "Alice"}]}

    # Patch DB call
    monkeypatch.setattr(handlers_dev.db, "get_user_by_telegram_id", mock_query_success)

    cache = {}
    # First call should hit DB and cache
    name1 = handlers_dev._id_to_name("123", cache)
    assert name1 == "Alice"
    assert calls["count"] == 1
    assert cache["123"] == "Alice"

    # Change the mock to raise, but cached value should be used and no new DB hit
    def mock_query_raise(telegram_id: str):
        raise RuntimeError("Should not be called due to cache")

    monkeypatch.setattr(handlers_dev.db, "get_user_by_telegram_id", mock_query_raise)

    name2 = handlers_dev._id_to_name("123", cache)
    assert name2 == "Alice"
    assert calls["count"] == 1  # no additional DB calls

    # Test fallback when no item returned; now should return and cache 'UNKNOWN'
    def mock_query_empty(telegram_id: str):
        return {"Items": []}

    monkeypatch.setattr(handlers_dev.db, "get_user_by_telegram_id", mock_query_empty)

    cache2 = {}
    name3 = handlers_dev._id_to_name("456", cache2)
    assert name3 == "UNKNOWN"
    assert cache2["456"] == "UNKNOWN"

    # Now even if DB returns a different name, cache should still be used
    def mock_query_new_name(telegram_id: str):
        return {"Items": [{"Name": "Bob"}]}

    monkeypatch.setattr(handlers_dev.db, "get_user_by_telegram_id", mock_query_new_name)

    name4 = handlers_dev._id_to_name("456", cache2)
    assert name4 == "UNKNOWN"  # cached fallback retained


# ---------------------------------------------------------------------------
# Developer & Admin Tools Rich Message Tests
# ---------------------------------------------------------------------------

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from pyrogram.errors import RichMessageUnsupported
from stoscbots.bot import keyboards
from stoscbots.util import bot_auth, utils


@pytest.fixture(autouse=True)
def neuter_metrics_and_super_admin(monkeypatch):
    monkeypatch.setattr(handlers_dev.loggers, "update_access_metrics", lambda uid: None)


def _make_admin_user(uid=1234):
    return SimpleNamespace(id=uid, username="admin_user", first_name="Admin")


def _make_non_admin_user(uid=9999):
    return SimpleNamespace(id=uid, username="regular_user", first_name="Parishioner")


@pytest.mark.asyncio
async def test_version_handler_rich(monkeypatch):
    client = SimpleNamespace(name="stoscbot", send_rich_message=AsyncMock())
    message = SimpleNamespace(
        from_user=_make_admin_user(),
        _client=SimpleNamespace(APP_VERSION="1.0.0", SYSTEM_VERSION="Linux 6.0"),
        reply_text=AsyncMock(),
        text="/version",
    )

    await handlers_dev.version_handler(client, message)

    client.send_rich_message.assert_awaited_once()
    args, kwargs = client.send_rich_message.await_args
    chat_id, rich_card = args
    assert chat_id == 1234
    assert kwargs["reply_markup"] == keyboards.back_to_main_keyboard

    # Verify Kurigram page serialization
    page = await rich_card.write(client=None)
    assert page.blocks


@pytest.mark.asyncio
async def test_version_handler_fallback(monkeypatch):
    client = SimpleNamespace(
        name="stoscbot",
        send_rich_message=AsyncMock(side_effect=RichMessageUnsupported()),
    )
    message = SimpleNamespace(
        from_user=_make_admin_user(),
        _client=SimpleNamespace(APP_VERSION="1.0.0", SYSTEM_VERSION="Linux 6.0"),
        reply_text=AsyncMock(),
        text="/version",
    )

    await handlers_dev.version_handler(client, message)

    message.reply_text.assert_awaited_once()
    fallback_text = message.reply_text.await_args.args[0]
    assert "Telegram Version:" in fallback_text
    assert message.reply_text.await_args.kwargs["reply_markup"] == keyboards.back_to_main_keyboard


@pytest.mark.asyncio
async def test_show_admin_menu_rich(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    client = SimpleNamespace(send_rich_message=AsyncMock())
    query = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Admin Menu",
    )

    await handlers_dev.show_admin_menu(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    args, kwargs = client.send_rich_message.await_args
    assert args[0] == 1234
    assert kwargs["reply_markup"] == keyboards.admin_menu_keyboard

    page = await args[1].write(client=None)
    assert page.blocks


@pytest.mark.asyncio
async def test_show_admin_menu_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    client = SimpleNamespace(send_rich_message=AsyncMock(side_effect=RichMessageUnsupported()))
    query = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Admin Menu",
    )
    mock_edit = AsyncMock()
    monkeypatch.setattr(utils, "edit_and_send_msg", mock_edit)

    await handlers_dev.show_admin_menu(client, query)

    mock_edit.assert_awaited_once()
    assert "Admin Menu" in mock_edit.await_args.args[1]


@pytest.mark.asyncio
async def test_show_admin_menu_unauthorized(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: False)
    client = SimpleNamespace(send_rich_message=AsyncMock())
    query = SimpleNamespace(
        from_user=_make_non_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Admin Menu",
    )

    await handlers_dev.show_admin_menu(client, query)

    query.answer.assert_awaited_once_with("You are not allowed to execute this action", show_alert=True)
    client.send_rich_message.assert_not_called()


@pytest.mark.asyncio
async def test_show_stats_linux_rich(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    monkeypatch.setattr(handlers_dev.platform, "system", lambda: "Linux")
    mock_run = MagicMock(return_value=SimpleNamespace(stdout=" 15 1234\n  5 5678\n"))
    monkeypatch.setattr(handlers_dev.subprocess, "run", mock_run)
    monkeypatch.setattr(handlers_dev, "_replace_ids_with_names", lambda res: "15 John Doe\n5 Jane Smith")

    client = SimpleNamespace(send_rich_message=AsyncMock())
    query = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Show Stats",
    )

    await handlers_dev.show_stats(client, query)

    query.answer.assert_awaited_once()
    client.send_rich_message.assert_awaited_once()
    args, kwargs = client.send_rich_message.await_args
    assert args[0] == 1234
    assert kwargs["reply_markup"] == keyboards.admin_menu_keyboard

    page = await args[1].write(client=None)
    assert page.blocks


@pytest.mark.asyncio
async def test_show_stats_linux_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    monkeypatch.setattr(handlers_dev.platform, "system", lambda: "Linux")
    mock_run = MagicMock(return_value=SimpleNamespace(stdout=" 15 1234\n"))
    monkeypatch.setattr(handlers_dev.subprocess, "run", mock_run)
    monkeypatch.setattr(handlers_dev, "_replace_ids_with_names", lambda res: "15 John Doe")

    client = SimpleNamespace(send_rich_message=AsyncMock(side_effect=RichMessageUnsupported()))
    query = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Show Stats",
    )
    mock_edit = AsyncMock()
    monkeypatch.setattr(utils, "edit_and_send_msg", mock_edit)

    await handlers_dev.show_stats(client, query)

    mock_edit.assert_awaited_once()
    assert "Top users by messages" in mock_edit.await_args.args[1]


@pytest.mark.asyncio
async def test_show_stats_non_linux(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    monkeypatch.setattr(handlers_dev.platform, "system", lambda: "Windows")

    client = SimpleNamespace(send_rich_message=AsyncMock())
    query = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Show Stats",
    )

    await handlers_dev.show_stats(client, query)

    client.send_rich_message.assert_awaited_once()
    args, kwargs = client.send_rich_message.await_args
    page = await args[1].write(client=None)
    assert page.blocks


@pytest.mark.asyncio
async def test_show_logs_rich_and_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    monkeypatch.setattr(handlers_dev.platform, "system", lambda: "Linux")
    mock_run = MagicMock(return_value=SimpleNamespace(stdout="2026-11-19 User action\n2026-11-19 Another action\n"))
    monkeypatch.setattr(handlers_dev.subprocess, "run", mock_run)

    # Test rich success
    client = SimpleNamespace(send_rich_message=AsyncMock())
    query = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Show Logs",
    )

    await handlers_dev.show_logs(client, query)

    client.send_rich_message.assert_awaited_once()
    page = await client.send_rich_message.await_args.args[1].write(client=None)
    assert page.blocks

    # Test rich fallback
    client_fallback = SimpleNamespace(send_rich_message=AsyncMock(side_effect=RichMessageUnsupported()))
    mock_edit = AsyncMock()
    monkeypatch.setattr(utils, "edit_and_send_msg", mock_edit)

    await handlers_dev.show_logs(client_fallback, query)
    mock_edit.assert_awaited_once()

    # Test non-linux
    monkeypatch.setattr(handlers_dev.platform, "system", lambda: "Windows")
    query_win = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Show Logs",
    )
    await handlers_dev.show_logs(client, query_win)
    query_win.message.reply_text.assert_awaited_once_with(
        "This action is only available when the bot runs on Linux.",
        reply_markup=keyboards.admin_menu_keyboard,
    )


@pytest.mark.asyncio
async def test_show_error_logs_rich_and_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    monkeypatch.setattr(handlers_dev.platform, "system", lambda: "Linux")
    mock_run = MagicMock(return_value=SimpleNamespace(stdout="2026-11-19 ERROR Exception detail\n"))
    monkeypatch.setattr(handlers_dev.subprocess, "run", mock_run)

    # Test rich success
    client = SimpleNamespace(send_rich_message=AsyncMock())
    query = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Show Error Logs",
    )

    await handlers_dev.show_error_logs(client, query)

    client.send_rich_message.assert_awaited_once()
    page = await client.send_rich_message.await_args.args[1].write(client=None)
    assert page.blocks

    # Test rich fallback
    client_fallback = SimpleNamespace(send_rich_message=AsyncMock(side_effect=RichMessageUnsupported()))
    mock_edit = AsyncMock()
    monkeypatch.setattr(utils, "edit_and_send_msg", mock_edit)

    await handlers_dev.show_error_logs(client_fallback, query)
    mock_edit.assert_awaited_once()

    # Test non-linux
    monkeypatch.setattr(handlers_dev.platform, "system", lambda: "Windows")
    query_win = SimpleNamespace(
        from_user=_make_admin_user(),
        answer=AsyncMock(),
        message=SimpleNamespace(reply_text=AsyncMock()),
        data="Show Error Logs",
    )
    await handlers_dev.show_error_logs(client, query_win)
    query_win.message.reply_text.assert_awaited_once_with(
        "This action is only available when the bot runs on Linux.",
        reply_markup=keyboards.admin_menu_keyboard,
    )


@pytest.mark.asyncio
async def test_get_telegram_id_handler_rich_success(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    monkeypatch.setattr(
        utils,
        "get_all_TelegramIDs_from_MemberCode",
        lambda code: [
            {"Name": "Vibin", "telegram_id": "22541119", "auth": ["mc"]},
            {"Name": "Family Member", "telegram_id": "88888888"},
        ],
    )
    client = SimpleNamespace(send_rich_message=AsyncMock())
    message = SimpleNamespace(
        from_user=_make_admin_user(),
        command=["id", "V019"],
        reply_text=AsyncMock(),
        text="/id V019",
    )

    await handlers_dev.get_telegram_id_handler(client, message)

    client.send_rich_message.assert_awaited_once()
    args, kwargs = client.send_rich_message.await_args
    assert args[0] == 1234
    page = await args[1].write(client=None)
    assert page.blocks
    markup = kwargs["reply_markup"]
    assert markup.inline_keyboard[0][0].callback_data == "related_family:V019"


@pytest.mark.asyncio
async def test_get_telegram_id_handler_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    monkeypatch.setattr(utils, "get_all_TelegramIDs_from_MemberCode", lambda code: [])
    monkeypatch.setattr(
        utils,
        "get_TelegramID_from_MemberCode",
        lambda code: {"Name": "Vibin", "telegram_id": "22541119"},
    )
    client = SimpleNamespace(send_rich_message=AsyncMock(side_effect=RichMessageUnsupported()))
    message = SimpleNamespace(
        from_user=_make_admin_user(),
        command=["id", "v019"],
        reply_text=AsyncMock(),
        text="/id v019",
    )

    await handlers_dev.get_telegram_id_handler(client, message)

    message.reply_text.assert_awaited_once()
    reply = message.reply_text.await_args.args[0]
    assert "**Member Details (V019)**" in reply
    assert "Vibin: `22541119`" in reply
    assert message.reply_text.await_args.kwargs["reply_markup"].inline_keyboard[0][0].callback_data == "related_family:V019"


@pytest.mark.asyncio
async def test_get_telegram_id_handler_not_found_rich_and_fallback(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    monkeypatch.setattr(utils, "get_all_TelegramIDs_from_MemberCode", lambda code: [])
    monkeypatch.setattr(utils, "get_TelegramID_from_MemberCode", lambda code: None)

    # Test rich not found
    client = SimpleNamespace(send_rich_message=AsyncMock())
    message = SimpleNamespace(
        from_user=_make_admin_user(),
        command=["id", "Z999"],
        reply_text=AsyncMock(),
        text="/id Z999",
    )

    await handlers_dev.get_telegram_id_handler(client, message)

    client.send_rich_message.assert_awaited_once()
    page = await client.send_rich_message.await_args.args[1].write(client=None)
    assert page.blocks

    # Test fallback not found
    client_fallback = SimpleNamespace(send_rich_message=AsyncMock(side_effect=RichMessageUnsupported()))
    await handlers_dev.get_telegram_id_handler(client_fallback, message)
    message.reply_text.assert_awaited_once_with(
        "Member not found: `Z999`",
        reply_markup=keyboards.get_member_id_keyboard("Z999"),
    )


@pytest.mark.asyncio
async def test_get_telegram_id_handler_invalid_code(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    client = SimpleNamespace()
    message = SimpleNamespace(
        from_user=_make_admin_user(),
        command=["id", "INVALID_123"],
        reply_text=AsyncMock(),
        text="/id INVALID_123",
    )

    await handlers_dev.get_telegram_id_handler(client, message)

    message.reply_text.assert_awaited_once_with("Invalid member code: `INVALID_123`")


@pytest.mark.asyncio
async def test_get_telegram_id_handler_missing_args(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: True)
    client = SimpleNamespace()
    message = SimpleNamespace(
        from_user=_make_admin_user(),
        command=["id"],
        reply_text=AsyncMock(),
        text="/id",
    )

    await handlers_dev.get_telegram_id_handler(client, message)

    message.reply_text.assert_awaited_once_with(
        "Please enter proper commands\ne.g. `/id [member_code]`"
    )


@pytest.mark.asyncio
async def test_get_telegram_id_handler_unauthorized(monkeypatch):
    monkeypatch.setattr(bot_auth, "is_super_admin", lambda uid: False)
    client = SimpleNamespace()
    message = SimpleNamespace(
        from_user=_make_non_admin_user(),
        command=["id", "V019"],
        reply_text=AsyncMock(),
        text="/id V019",
    )

    await handlers_dev.get_telegram_id_handler(client, message)

    message.reply_text.assert_awaited_once_with("You are not allowed to execute this command")


