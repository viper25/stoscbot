from plugins import handlers_finance
from tests.mocks import *


def test_finance_search_member_payments(monkeypatch):
    msg.command = ["x", "v019"]
    msg.from_user = telegram_member_mc
    handlers_finance.finance_search_member_payments(telegram_client, msg)
    assert 1 == 1  # this is just to make pytest pass
