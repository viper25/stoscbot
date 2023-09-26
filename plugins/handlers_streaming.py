import logging
import os
import platform
import subprocess

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from stoscbots.util import loggers
from stoscbots.util.loggers import LOGLEVEL

logger = logging.getLogger('Handler.Streaming')
logger.setLevel(LOGLEVEL)

ANNOUNCEMENTS_SLIDES_DIR = '~/jobs/stosc_announcements/announcements-slides'
ANNOUNCEMENTS_SLIDES_SCRIPT = 'launcher_slide_generator.sh'


def dynamic_data_filter(data):
    return filters.create(
        lambda flt, _, query: query.data.startswith(flt.data), data=data
    )


@Client.on_callback_query(dynamic_data_filter("Generate Announcement Slides"))
@loggers.async_log_access
async def generate_announcement_slides(client: Client, query: CallbackQuery):
    await query.answer()

    # Check if the system is Linux
    if platform.system() == "Linux":
        # Generate the slides
        cmd = f"cd {ANNOUNCEMENTS_SLIDES_DIR} && ./{ANNOUNCEMENTS_SLIDES_SCRIPT}"
        logger.info(f"Executing {cmd}")
        subprocess.run(cmd)

        # Optionally send a message to the user indicating that the script was triggered
        await query.message.reply_text("Triggered Announcement slides generation")
    else:
        # Optionally inform the user that this action is only available on Linux
        await query.message.reply_text("This action is only available when the bot runs on Linux.")
