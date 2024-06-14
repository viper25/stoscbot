import logging
import os
from datetime import datetime

from convopyro import Conversation
from pyrogram import Client

from stoscbots.util.loggers import LOGLEVEL

# ------------------------------------------------------------------
# Module logger
logger = logging.getLogger('Bot')
logger.setLevel(LOGLEVEL)
logger.info(f"Log Level: {LOGLEVEL}. Set in Environment Variable LOGLEVEL")
# ------------------------------------------------------------------

test_mode = True
ENV = os.environ.get("ENV")
env_banner = """
    ▀▀█▀▀ █▀▀ █▀▀ ▀▀█▀▀ 
    ░▒█░░ █▀▀ ▀▀█ ░░█░░ 
    ░▒█░░ ▀▀▀ ▀▀▀ ░░▀░░
    """
if ENV == "PRO":
    test_mode = False
    env_banner = """
    ▒█▀▀█ █▀▀█ █▀▀█ █▀▀▄ █░░█ █▀▀ ▀▀█▀▀ ░▀░ █▀▀█ █▀▀▄ 
    ▒█▄▄█ █▄▄▀ █░░█ █░░█ █░░█ █░░ ░░█░░ ▀█▀ █░░█ █░░█ 
    ▒█░░░ ▀░▀▀ ▀▀▀▀ ▀▀▀░ ░▀▀▀ ▀▀▀ ░░▀░░ ▀▀▀ ▀▀▀▀ ▀░░▀
    """

logger.info("""\n
░██████╗████████╗░█████╗░░██████╗░█████╗░  ██████╗░░█████╗░████████╗
██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗  ██╔══██╗██╔══██╗╚══██╔══╝
╚█████╗░░░░██║░░░██║░░██║╚█████╗░██║░░╚═╝  ██████╦╝██║░░██║░░░██║░░░
░╚═══██╗░░░██║░░░██║░░██║░╚═══██╗██║░░██╗  ██╔══██╗██║░░██║░░░██║░░░
██████╔╝░░░██║░░░╚█████╔╝██████╔╝╚█████╔╝  ██████╦╝╚█████╔╝░░░██║░░░
╚═════╝░░░░╚═╝░░░░╚════╝░╚═════╝░░╚════╝░  ╚═════╝░░╚════╝░░░░╚═╝░░░
"""
      )
logger.info(f"Environment:\n{env_banner}")

# Initialization. Values from https://my.telegram.org/apps
# When asked "Enter phone number or bot token:", enter ONLY bot token

# api_id = XXX
# api_hash = "XXX"
# app = Client(os.environ.get("BOT_CLIENT_NAME"), plugins=dict(root="plugins"), api_id=api_id, api_hash=api_hash)

app = Client(os.environ.get("BOT_CLIENT_NAME"), plugins=dict(root="plugins"), test_mode=test_mode)
Conversation(app)


def run():
    app.start_time = datetime.now()
    logger.info(f"Version: {app.APP_VERSION} on {app.SYSTEM_VERSION}")
    app.run()
