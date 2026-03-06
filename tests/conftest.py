import asyncio


def pytest_configure(config):
    """Ensure an event loop exists before any module imports (e.g. pyrogram) that
    call asyncio.get_event_loop() at import time, which raises a DeprecationWarning
    in Python 3.10+ when no current event loop is set."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

