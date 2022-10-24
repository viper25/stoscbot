from pyrogram import Client, filters
from pyrogram.types import Message
from stoscbots.util import loggers, bot_auth
import configparser

@Client.on_message(filters.command(["version","ver"]))
@loggers.async_log_access
@bot_auth.async_management_only
async def version_handler(client: Client, message: Message):

    config = configparser.ConfigParser()
    config.read(r'.VERSION')
    msg = f"Telegram Version: **{message._client.APP_VERSION}** on **{message._client.SYSTEM_VERSION}**"
    msg += f"\nSession Name: **{client.name}**\n"
    msg += "-------------"
    msg += f"\nRelease Version: `{config.get('version', 'VERSION')}`"
    msg += f"\nRelease Date: `{config.get('version', 'RELEASE_DATE')}`"
    msg += f"\nBuild SHA: `{config.get('version', 'BUILD')[:7]}`"
    msg += f"\nBranch: `{config.get('version', 'BRANCH')}`"
    
    await message.reply_text(msg)