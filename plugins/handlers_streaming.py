import datetime
import logging
import os
import platform
import subprocess
from tempfile import NamedTemporaryFile

import requests
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, LinkPreviewOptions

from stoscbots.util import loggers, utils, bot_auth
from stoscbots.util.loggers import LOGLEVEL
from stoscbots.util.utils import get_telegram_file_url

logger = logging.getLogger('Handler.Streaming')
logger.setLevel(LOGLEVEL)

STOSCBOT_APP_HOME_DIR = os.environ.get('STOSCBOT_APP_HOME_DIR')

ANNOUNCEMENTS_SLIDES_DIR = f"/home/{STOSCBOT_APP_HOME_DIR}/jobs/stosc_announcements/announcements-slides"
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
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        # Optionally send a message to the user indicating that the script was triggered
        await query.message.reply_text(f"Started slides generation... ⏳`{result}`"
                                       f"\n\nCheck [Google Drive](https://drive.google.com/drive/folders/13YnRvL9JZoGbeMXQ1T9E7vhaEZEFfUK8) for the slides.")
    else:
        # Optionally inform the user that this action is only available on Linux
        await query.message.reply_text("This action is only available when the bot runs on Linux.")


@Client.on_message(filters.photo)
@loggers.async_log_access
@bot_auth.async_management_only
async def generate_image_url(client: Client, message: Message):
    photo = message.photo
    logger.info(f"Uploading image ({round(photo.file_size / 1024)} Kb)")

    file_url = await get_telegram_file_url(photo)

    temp_file_flag = False if os.environ.get('OS') == 'Windows_NT' else True
    with NamedTemporaryFile(delete=temp_file_flag) as tf:
        # Download the file from file_url
        response = requests.get(file_url)
        tf.write(response.content)

        dt = (datetime.datetime.now()).strftime("%Y_%m_%d_%H_%M_%S")
        image_name = f"announcement_images/{dt}_{photo.file_unique_id}.jpg"
        url = utils.upload_to_s3_and_get_url(image_file=tf, object_name=image_name)
        tf.flush()

    await message.reply_text(f"URL: \n\n{url}", link_preview_options=LinkPreviewOptions(is_disabled=True))
