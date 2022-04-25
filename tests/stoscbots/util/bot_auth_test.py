import os
from stoscbots.util import bot_auth
from tests.mocks import *

telegram_query = CallbackQuery(id="123456", from_user=telegram_member_mc, chat_instance="0")


def test_is_member_True():
    assert bot_auth.is_member(os.environ.get("VIBIN_TELEGRAM_ID")) is True
    assert bot_auth.is_member(telegram_member_mc.id) is True
    assert bot_auth.is_member(telegram_member_area_prayer_coordinator.id) is True
    assert bot_auth.is_member(telegram_member_harvest_admin.id) is True
    assert bot_auth.is_member(telegram_member_normal.id) is True
    assert bot_auth.is_member(telegram_member_smo.id) is True
    assert bot_auth.is_member(telegram_member_stmarys.id) is True


def test_is_member_False():
    assert bot_auth.is_member(telegram_member_non) is None


def test_is_mgmt_member_True():
    assert bot_auth.is_mgmt_member(os.environ.get("VIBIN_TELEGRAM_ID")) is True
    assert bot_auth.is_mgmt_member(telegram_member_mc.id) is True


def test_is_mgmt_member_False():
    assert bot_auth.is_mgmt_member(telegram_member_area_prayer_coordinator.id) is None
    assert bot_auth.is_mgmt_member(telegram_member_harvest_admin.id) is None
    assert bot_auth.is_mgmt_member(telegram_member_non.id) is None
    assert bot_auth.is_mgmt_member(telegram_member_normal.id) is None
    assert bot_auth.is_mgmt_member(telegram_member_smo.id) is None
    assert bot_auth.is_mgmt_member(telegram_member_stmarys.id) is None


def test_is_smo_member_True():
    assert bot_auth.is_smo_member(os.environ.get("VIBIN_TELEGRAM_ID")) is True
    assert bot_auth.is_smo_member(telegram_member_smo.id) is True
    assert bot_auth.is_smo_member(telegram_member_mc.id) is True


def test_is_smo_member_False():
    assert bot_auth.is_smo_member(telegram_member_area_prayer_coordinator.id) is None
    assert bot_auth.is_smo_member(telegram_member_harvest_admin.id) is None
    assert bot_auth.is_smo_member(telegram_member_non.id) is None
    assert bot_auth.is_smo_member(telegram_member_normal.id) is None
    assert bot_auth.is_smo_member(telegram_member_stmarys.id) is None


def test_is_area_prayer_coordinator_True():
    assert bot_auth.is_area_prayer_coordinator_member(os.environ.get("VIBIN_TELEGRAM_ID")) is True
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_area_prayer_coordinator.id) is True
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_mc.id) is True


def test_is_area_prayer_coordinator_member_False():
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_smo.id) is None
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_harvest_admin.id) is None
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_non.id) is None
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_normal.id) is None
    assert bot_auth.is_area_prayer_coordinator_member(telegram_member_stmarys.id) is None


def test_is_st_marys_member_member_True():
    assert bot_auth.is_st_marys_member(os.environ.get("VIBIN_TELEGRAM_ID")) is True
    assert bot_auth.is_st_marys_member(telegram_member_stmarys.id) is True
    assert bot_auth.is_st_marys_member(telegram_member_mc.id) is True


def test_is_st_marys_member_False():
    assert bot_auth.is_st_marys_member(telegram_member_smo.id) is None
    assert bot_auth.is_st_marys_member(telegram_member_harvest_admin.id) is None
    assert bot_auth.is_st_marys_member(telegram_member_non.id) is None
    assert bot_auth.is_st_marys_member(telegram_member_normal.id) is None
    assert bot_auth.is_st_marys_member(telegram_member_area_prayer_coordinator.id) is None


def test_decorator_member_only(monkeypatch):
    @bot_auth.async_member_only
    def to_be_decorated_fn(telegram_client, telegram_query):
        # If Non-member then this function isn't called and nothing is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_harvest_admin
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_smo
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_stmarys
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"


def test_decorator_management_only(monkeypatch):
    @bot_auth.management_only
    def to_be_decorated_fn(telegram_client, telegram_query):
        # If Non-member then this function isn't called and nothing is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_harvest_admin
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_smo
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_stmarys
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None


def test_decorator_area_prayer_coordinator_only(monkeypatch):
    @bot_auth.area_prayer_coordinator_only
    def to_be_decorated_fn(telegram_client, telegram_query):
        # If Non-member then this function isn't called and nothing is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_harvest_admin
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_smo
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_stmarys
    value = to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None
