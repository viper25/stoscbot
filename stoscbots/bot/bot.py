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
MODE = os.environ.get("MODE")
if MODE == "PRO":
    test_mode = False

app = Client("STOSCBOT_Laptop", plugins=dict(root="plugins"), test_mode=test_mode)

def run():
    app.start_time = datetime.now()
    logger.info(f"Version: {app.APP_VERSION} on {app.SYSTEM_VERSION}")
    app.run()
