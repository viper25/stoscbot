from typing import Coroutine

from stoscbots.util import bot_auth
from stoscbots.util.bot_auth import get_super_admin_id, VIBIN_TELEGRAM_ID
from tests.mocks import *

telegram_query = CallbackQuery(id="123456", from_user=telegram_member_mc, chat_instance="0")


def test_is_member_True():
    assert bot_auth.is_member(bot_auth.get_super_admin_id()) is True
    assert bot_auth.is_member(telegram_member_mc.id) is True
    assert bot_auth.is_member(telegram_member_area_prayer_coordinator.id) is True
    assert bot_auth.is_member(telegram_member_harvest_admin.id) is True
    assert bot_auth.is_member(telegram_member_normal.id) is True


def test_is_member_False():
    assert bot_auth.is_member(telegram_member_non) is None


def test_is_mgmt_member_True():
    assert bot_auth.is_mgmt_member(bot_auth.get_super_admin_id()) is True
    assert bot_auth.is_mgmt_member(telegram_member_mc.id) is True


def test_is_mgmt_member_False():
    assert bot_auth.is_mgmt_member(telegram_member_area_prayer_coordinator.id) is None
    assert bot_auth.is_mgmt_member(telegram_member_harvest_admin.id) is None
    assert bot_auth.is_mgmt_member(telegram_member_non.id) is None
    assert bot_auth.is_mgmt_member(telegram_member_normal.id) is None


def test_is_area_prayer_coordinator_True():
    assert bot_auth.is_area_prayer_coordinator_member(bot_auth.get_super_admin_id()) is True
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_area_prayer_coordinator.id) is True
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_mc.id) is True


def test_is_area_prayer_coordinator_member_False():
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_harvest_admin.id) is None
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_non.id) is None
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_normal.id) is None


@pytest.mark.asyncio
async def test_decorator_member_only(monkeypatch):
    @bot_auth.async_member_only
    async def to_be_decorated_fn(telegram_client, telegram_query):
        # If access denied then this function isn't called and only a Coroutine is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert isinstance(value, Coroutine)

    telegram_query.from_user = telegram_member_harvest_admin
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"


@pytest.mark.asyncio
async def test_decorator_management_only(monkeypatch):
    @bot_auth.async_management_only
    async def to_be_decorated_fn(telegram_client, telegram_query):
        # If access denied then this function isn't called and only a Coroutine is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert isinstance(value, Coroutine)

    telegram_query.from_user = telegram_member_harvest_admin
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert isinstance(value, Coroutine)

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert isinstance(value, Coroutine)


@pytest.mark.asyncio
async def test_decorator_area_prayer_coordinator_only(monkeypatch):
    @bot_auth.async_area_prayer_coordinator_only
    async def to_be_decorated_fn(telegram_client, telegram_query):
        # If access denied then this function isn't called and only a Coroutine is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert isinstance(value, Coroutine)

    telegram_query.from_user = telegram_member_harvest_admin
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert isinstance(value, Coroutine)

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert isinstance(value, Coroutine)
