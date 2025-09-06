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

    # Test fallback when no item returned; also ensure it caches the id itself
    def mock_query_empty(telegram_id: str):
        return {"Items": []}

    monkeypatch.setattr(handlers_dev.db, "get_user_by_telegram_id", mock_query_empty)

    cache2 = {}
    name3 = handlers_dev._id_to_name("456", cache2)
    assert name3 == "456"
    assert cache2["456"] == "456"

    # Now even if DB returns a different name, cache should still be used
    def mock_query_new_name(telegram_id: str):
        return {"Items": [{"Name": "Bob"}]}

    monkeypatch.setattr(handlers_dev.db, "get_user_by_telegram_id", mock_query_new_name)

    name4 = handlers_dev._id_to_name("456", cache2)
    assert name4 == "456"  # cached fallback retained

