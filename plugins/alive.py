import asyncio
import platform
import subprocess
import time
from datetime import datetime
from secrets import choice
from pytz import timezone as tz
from telethon import Button, events
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError
from telethon.utils import get_display_name
from datetime import datetime
from telethon import Button, events
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError
from telethon.utils import get_display_name

from pyUltroid._misc import SUDO_M, owner_and_sudos
from pyUltroid.dB.base import KeyManager
from pyUltroid.fns.helper import inline_mention
from strings import get_string

from pyUltroid._misc import SUDO_M, owner_and_sudos
from pyUltroid.dB.base import KeyManager
from pyUltroid.fns.helper import inline_mention
from telethon.tl.types import InputMessagesFilterVideo, InputMessagesFilterVoice
from telethon.tl.types import InputMessagesFilterPhotos
from platform import python_version as pyver
from pyrogram.enums import ChatType
from pyrogram import __version__ as pver
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButton
#from telethon.tl.types import KeyboardButton
from telegram import __version__ as lver
from telethon import __version__ as tver
from pytgcalls import __version__ as pytver
from pyrogram import filters
from pyrogram.types import Message
from telethon import TelegramClient, events
from telethon.tl.custom import Button
from . import *
from . import ultroid_bot as client
import resources
from pyUltroid.fns.helper import inline_mention

async def member_permissions(chat_id: int, user_id: int):
    perms = []
    member = (await ultroid_bot.get_chat_member(chat_id, user_id)).privileges
    if not member:
        return []
    if member.can_post_messages:
        perms.append("can_post_messages")
    if member.can_edit_messages:
        perms.append("can_edit_messages")
    if member.can_delete_messages:
        perms.append("can_delete_messages")
    if member.can_restrict_members:
        perms.append("can_restrict_members")
    if member.can_promote_members:
        perms.append("can_promote_members")
    if member.can_change_info:
        perms.append("can_change_info")
    if member.can_invite_users:
        perms.append("can_invite_users")
    if member.can_pin_messages:
        perms.append("can_pin_messages")
    if member.can_manage_video_chats:
        perms.append("can_manage_video_chats")
    return perms

PHOTO = [
    "https://files.catbox.moe/hen0og.jpg"
]

Mukesh = [
    [
        Button.url("ɴᴏᴏʙ", url=f"https://t.me/{OWNER_USERNAME}"),
        Button.url("ꜱᴜᴘᴘᴏʀᴛ", url=f"https://t.me/xteam_cloner"),
    ],
    [
        Button.url("➕ᴀᴅᴅ ᴍᴇ ᴇʟsᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ➕",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
]

message_text = f"<blockquote>ʜᴇʏ, ɪ ᴀᴍ {BOT_NAME} 🥀</blockquote>\n<blockquote>» ᴍʏ ᴏᴡɴᴇʀ : {OWNER_NAME}\n\n» ʟɪʙʀᴀʀʏ ᴠᴇʀsɪᴏɴ : {lver}\n\n» ᴛᴇʟᴇᴛʜᴏɴ ᴠᴇʀsɪᴏɴ : {tver}\n\n» ᴘʏʀᴏɢʀᴀᴍ ᴠᴇʀsɪᴏɴ : {pver}\n\n» ᴘʏᴛʜᴏɴ ᴠᴇʀsɪᴏɴ : {pyver()}\n\n Uptime : {uptime}\n</blockquote>"


@ultroid_cmd(pattern="alive$")
async def alive(event):
    start = time.time()
    pro = await event.eor("⚡")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    await asyncio.sleep(3)
    await pro.delete()
    owner=await ultroid_bot.get_users(OWNER_ID)
    await event.client.send_message(event.chat.id, message_text, parse_mode="html")
    

@ultroid_cmd(pattern="Alive$")
async def alive(event):
    try:
        asupannya = [
            asupan
            async for asupan in event.client.iter_messages(
                "@xcryasupan", filter=InputMessagesFilterVideo
            )
        ]

        if not asupannya:
            await event.respond("No video found in @xcryasupan.")
            return

        pro = await event.eor("⚡")
        await asyncio.sleep(2)
        await pro.delete()

        owner=await ultroid_bot.get_users(OWNER_ID)
        await event.client.send_file(
            event.chat.id,
            file=random.choice(asupannya),
            caption=message_text, # format the message_text
            parse_mode="html",
        )

    except Exception as e:
        await event.respond(f"An error occurred: {e}")
        
