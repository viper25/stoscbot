import os
import subprocess
from plugins.handlers_area_prayer_groups import dynamic_data_filter
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from stoscbots.db import db
from stoscbots.util import loggers, utils, bot_auth
from stoscbots.bot import keyboards
from dateutil import parser


announcements_slides_dir = '~/announcements-slides'
announcements_slides_script = os.path.join(announcements_slides_dir, 'announcement_google_generator.py')

def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data), data=data  # "data" kwarg is accessed with "flt.data" above
    )

@Client.on_callback_query(dynamic_data_filter("Generate Announcement Slides"))
@loggers.async_log_access
async def generate_announcement_slides(client: Client, query: CallbackQuery):
    await query.answer()  # Optionally send a notification to the user that the button was clicked    
    
    # Generate the slides
    subprocess.run(['python3', announcements_slides_script])
        
    # Optionally send a message to the user indicating that the script was triggered
    await query.message.reply_text("Triggered Announcement slides generation")
