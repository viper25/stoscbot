import os
from datetime import datetime
from pyrogram import Client

client = Client(session_name="stoscbot", bot_token=os.environ.get('STOSC_TELEGRAM_BOT_TOKEN'))
    
def run():
    client.start_time = datetime.now()
    client.run()