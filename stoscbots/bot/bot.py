import os
from datetime import datetime
from pyrogram import Client
from stoscbots.util.loggers import LOGLEVEL
import logging

# ------------------------------------------------------------------
# Module logger
logger = logging.getLogger('Bot')
logger.setLevel(LOGLEVEL)
# ------------------------------------------------------------------

test_mode = True
ENV = os.environ.get("ENV")
if ENV == "PRO":
    test_mode = False

app = Client(os.environ.get("BOT_CLIENT_NAME"), plugins=dict(root="plugins"), test_mode=test_mode)

def run():
    app.start_time = datetime.now()
    logger.info(f"Version: {app.APP_VERSION} on {app.SYSTEM_VERSION}")
    app.run()
