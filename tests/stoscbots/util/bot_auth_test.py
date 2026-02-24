from stoscbots.util import bot_auth
from stoscbots.util.bot_auth import get_super_admin_id, VIBIN_TELEGRAM_ID, is_super_admin, get_super_admin_ids
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

# --------------------------------------------------
@pytest.mark.asyncio
async def test_decorator_member_only(monkeypatch):
    async def fake_send_access_denied_msg(*_args, **_kwargs):
        return None

    monkeypatch.setattr(bot_auth, "send_access_denied_msg", fake_send_access_denied_msg)

    @bot_auth.async_member_only
    async def to_be_decorated_fn(telegram_client, telegram_query):
        # If access denied then this function isn't called and only a Coroutine is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_harvest_admin
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

# --------------------------------------------------
@pytest.mark.asyncio
async def test_decorator_management_only(monkeypatch):
    async def fake_send_access_denied_msg(*_args, **_kwargs):
        return None

    monkeypatch.setattr(bot_auth, "send_access_denied_msg", fake_send_access_denied_msg)

    @bot_auth.async_management_only
    async def to_be_decorated_fn(telegram_client, telegram_query):
        # If access denied then this function isn't called and only a Coroutine is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_harvest_admin
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

# --------------------------------------------------
@pytest.mark.asyncio
async def test_decorator_area_prayer_coordinator_only(monkeypatch):
    async def fake_send_access_denied_msg(*_args, **_kwargs):
        return None

    monkeypatch.setattr(bot_auth, "send_access_denied_msg", fake_send_access_denied_msg)

    @bot_auth.async_area_prayer_coordinator_only
    async def to_be_decorated_fn(telegram_client, telegram_query):
        # If access denied then this function isn't called and only a Coroutine is returned
        return "In Function"

    telegram_query.from_user = telegram_member_mc
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    telegram_query.from_user = telegram_member_non
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_harvest_admin
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value is None

    telegram_query.from_user = telegram_member_area_prayer_coordinator
    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

    value = await to_be_decorated_fn(telegram_client, telegram_query)
    assert value == "In Function"

# --------------------------------------------------
def test_get_super_admin_id():
    # Test if the function returns the expected constant value
    assert get_super_admin_id() == VIBIN_TELEGRAM_ID
# --------------------------------------------------
@pytest.fixture(autouse=True)
def mock_super_admin_ids(monkeypatch):
    ids = "1234,5678,9012"
    monkeypatch.setattr('stoscbots.util.bot_auth.get_super_admin_ids', lambda: ids)

def test_is_super_admin_true():
    assert is_super_admin(1234) is True
    assert is_super_admin(5678) is True
    assert is_super_admin(9012) is True

def test_is_super_admin_false():
    assert is_super_admin(3456) is False
    assert is_super_admin(7890) is False

def test_non_digit_in_env_var(monkeypatch):
    monkeypatch.setattr('stoscbots.util.bot_auth.get_super_admin_ids', lambda: "1234,abcd,9012")
    assert is_super_admin(1234) is True
    assert is_super_admin(9012) is True
    assert is_super_admin(3456) is False

def test_empty_env_var(monkeypatch):
    monkeypatch.setattr('stoscbots.util.bot_auth.get_super_admin_ids', lambda: "")
    assert is_super_admin(1234) is False

# --------------------------------------------------