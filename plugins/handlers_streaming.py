import datetime
import logging
import os
import platform
import subprocess
from tempfile import NamedTemporaryFile

import requests
from pyrogram import Client, filters
from pyrogram.errors import RichMessageUnsupported
from pyrogram.types import CallbackQuery, LinkPreviewOptions, Message

from stoscbots.bot import keyboards
from stoscbots.util import bot_auth, loggers, utils
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
@bot_auth.async_management_only
async def generate_announcement_slides(client: Client, query: CallbackQuery):
    await query.answer()
    chat_id = query.from_user.id

    is_linux = platform.system() == "Linux"
    returncode = None
    cmd_output = ""
    if is_linux:
        cmd = f"cd {ANNOUNCEMENTS_SLIDES_DIR} && ./{ANNOUNCEMENTS_SLIDES_SCRIPT}"
        logger.info(f"Executing {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        returncode = result.returncode
        cmd_output = (result.stdout or result.stderr or "").strip()

    fallback = (
        f"Started slides generation... ⏳ `{cmd_output}`\n\n"
        f"Check [Google Drive](https://drive.google.com/drive/folders/13YnRvL9JZoGbeMXQ1T9E7vhaEZEFfUK8) for the slides."
        if is_linux else
        "This action is only available when the bot runs on Linux."
    )

    try:
        rich_card = keyboards.get_rich_slide_generation_result(is_linux, returncode)
        await client.send_rich_message(
            chat_id,
            rich_card,
            reply_markup=keyboards.streaming_menu_keyboard,
        )
    except RichMessageUnsupported:
        await client.send_message(
            chat_id,
            fallback,
            reply_markup=keyboards.streaming_menu_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


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
