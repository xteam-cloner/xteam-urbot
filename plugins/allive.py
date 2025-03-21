import os
import asyncio
import platform
import subprocess
import time
import random
from datetime import datetime
from secrets import choice
from telethon import Button, events
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError
from telethon.utils import get_display_name
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError
from telethon.utils import get_display_name
from telethon.tl.types import InputMessagesFilterVideo, InputMessagesFilterVoice, InputMessagesFilterPhotos

from pyUltroid._misc import SUDO_M, owner_and_sudos
from pyUltroid.dB.base import KeyManager
from pyUltroid.fns.helper import inline_mention
from strings import get_string

from pyUltroid._misc import SUDO_M, owner_and_sudos
from pyUltroid.dB.base import KeyManager
from pyUltroid.fns.helper import inline_mention

from platform import python_version as pyver
from pyrogram import __version__ as pver
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
from . import (
    OWNER_NAME,
    OWNER_ID,
    BOT_NAME,
    OWNER_USERNAME,
    asst,
    start_time,
    time_formatter,
    udB,
    ultroid_cmd as xteam_cmd,
    get_string,
    ultroid_bot as client,
    eor,
    ultroid_bot,
    call_back,
    callback,
)

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

def format_message_text(uptime):
    return f"<blockquote>ʜᴇʏ, ɪ ᴀᴍ {BOT_NAME} 🥀</blockquote>\n" \
           f"<blockquote>❍ ᴍʏ ᴏᴡɴᴇʀ : {OWNER_NAME}\n" \
           f"❍ ʟɪʙʀᴀʀʏ : {lver}\n" \
           f"❍ ᴜᴘᴛɪᴍᴇ : {uptime}\n" \
           f"❍ ᴛᴇʟᴇᴛʜᴏɴ : {tver}\n" \
           f"❍ ᴘʏʀᴏɢʀᴀᴍ : {pver}\n" \
           f"❍ ᴘʏ-ᴛɢᴄᴀʟʟꜱ : {pytver}\n" \
           f"❍ ᴘʏᴛʜᴏɴ : {pyver()}\n</blockquote>"

@xteam_cmd(pattern="alive$")
async def alive(event):
    start = time.time()
    pro = await event.eor("⚡")
    await asyncio.sleep(2)
    await pro.delete()
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    message_text = format_message_text(uptime)
    await event.client.send_message(event.chat.id, message_text, parse_mode="html")

@xteam_cmd(pattern="Alive$")
async def alive_video(event):
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

        uptime = time_formatter((time.time() - start_time) * 1000)
        message_text = format_message_text(uptime)

        await event.client.send_file(
            event.chat.id,
            file=random.choice(asupannya),
            caption=message_text,
            parse_mode="html",
        )

    except Exception as e:
        await event.respond(f"An error occurred: {e}")
                     
