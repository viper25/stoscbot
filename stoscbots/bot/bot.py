import os
from datetime import datetime
from pyrogram import Client

client = Client(session_name="stoscbot", api_id=os.environ.get('PYROGRAM_API_ID'), api_hash=os.environ.get('PYROGRAM_API_HASH'), device_model=os.environ.get('PYROGRAM_DEVICE_MODEL'), system_version=os.environ.get('PYROGRAM_SYSTEM_VERSION') bot_token=os.environ.get('STOSC_TELEGRAM_BOT_TOKEN'))
    
def run():
    client.start_time = datetime.now()
    client.run()