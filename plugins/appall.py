from telethon import TelegramClient, events

from . import *

@ultroid_cmd(pattern="approveall")
async def approve_all(event):
        chat_id = event.chat_id
        try:
            await ultroid_bot.approve_chat_join_request(chat_id)
            await event.respond("Done")
            await event.delete()
        except Exception as e:
            await event.respond(f"Error: {e}")
