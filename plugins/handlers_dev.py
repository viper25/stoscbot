from pyrogram import Client, filters
from pyrogram.types import Message
from stoscbots.util import loggers, bot_auth

BOT_VERSION = "2.0.6"

# ==================================================
# Command Handlers
@Client.on_message(filters.command(["version","ver"]))
@loggers.async_log_access
@bot_auth.async_management_only
async def version_handler(client: Client, message: Message):
    msg = f"**STOSC Bot `{BOT_VERSION}`**\n➖➖➖➖➖\n"
    msg += f"►Version: **{message._client.APP_VERSION}** on **{message._client.SYSTEM_VERSION}**"
    msg += f"\n►Session Name: **{client.name}**"
    msg += f"\n►Bot Name: **{client.username}**"
    await message.reply_text(msg)
