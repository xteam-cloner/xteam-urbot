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

from xteam._misc import SUDO_M, owner_and_sudos
from xteam.dB.base import KeyManager
from xteam.fns.helper import inline_mention
from strings import get_string
from platform import python_version as pyver
from pyrogram import __version__ as pver
from xteam.version import __version__
from xteam.version import ultroid_version
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
from xteam.fns.helper import inline_mention
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


def format_message_text(uptime):
    return f"<blockquote><b>✰ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✰</b></blockquote>\n" \
                       f"✵ Owner : <a href='https://t.me/{OWNER_USERNAME}'>{OWNER_NAME}</a>\n" \
                       f"✵ Userbot : {ultroid_version}\n" \
                       f"✵ Dc Id : {ultroid_bot.dc_id}\n" \
                       f"✵ Library : {__version__}\n" \
                       f"✵ Uptime : {uptime}\n" \
                       f"✵ Kurigram :  {pver}\n" \
                       f"✵ Python : {pyver()}\n" \
                       f"<blockquote>✵ <a href='https://t.me/xteam_cloner'>xᴛᴇᴀᴍ ᴄʟᴏɴᴇʀ</a> ✵</blockquote>\n"

@xteam_cmd(pattern="live$")
async def alive(event):
    start = time.time()
    pro = await event.eor("🔥")
    await asyncio.sleep(0,5)
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    message_text = format_message_text(uptime)
    xpic = udB.get_key("ALIVE_PIC")
    xnone = ["false", "0", "none"] 
    xdefault = "resources/extras/IMG_20251027_112615_198.jpg"
    if xpic and str(xpic).lower() in xnone:
        pic = None    
    elif xpic and str(xpic).lower() in ["true", "1"]:
        pic = xdefault
    elif xpic:
        pic = xpic  
    else:
        pic = xdefault
    if pic:
        await pro.edit(message_text,
                       parse_mode="html",
                       file=pic
                      )
    else:
        await pro.edit(message_text,
                       parse_mode="html"
                      )
        
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
        await asyncio.sleep(1)
        await pro.delete()
        uptime = time_formatter((time.time() - start_time) * 1000000)
        message_text = format_message_text(uptime)

        selected_video_message = random.choice(asupannya)

        # Print information about the selected video message for debugging
        print(f"Selected video message ID: {selected_video_message.id}")
        if selected_video_message.video:
            print(f"Selected video attributes: {selected_video_message.video}")
            # Try to send the video directly
            await client.send_file(
                event.chat.id,
                file=selected_video_message.video, # Pass the video object
                caption=message_text,
                parse_mode="html",
            )
        else:
            await event.respond("Selected message does not contain a video.")


    except Exception as e:
        await event.respond(f"An error occurred: {e}")
from telethon.tl.types import User, Channel, Chat
from . import ultroid_cmd, ultroid_bot, start_time 
import time
from datetime import timedelta

START_TIME = start_time 

client = ultroid_bot 

@ultroid_cmd(pattern="status(| (.*))$", fullsudo=True)
async def status_checker(event):
    await event.edit("🔄 Mengambil status klien...")
    
    try:
        me = await event.client.get_me()
        is_premium = getattr(me, 'premium', False)
        dc_id = event.client.session.dc_id
    except Exception:
        is_premium = False
        dc_id = 'Unknown'

    try:
        ping_result = await event.client.ping_service(dc_id=dc_id)
        ping_dc = ping_result.get('duration', float('inf')) * 1000
    except Exception:
        ping_dc = float('inf')

    current_time = time.time()
    uptime_seconds = current_time - START_TIME
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))
    
    peer_users_status = "unlimited" if is_premium else "standard (500)"
    peer_group_status = "unlimited" if is_premium else "standard (200)"
    
    status_level = "Ultra Max" if is_premium else "Standard"
    
    output = (
        f"**Status: [{status_level}]**\n"
        "--------------------------------------------------\n"
        f"    `is_premium:` `{is_premium}`\n"
        f"    `peer_users:` `{peer_users_status}`\n"
        f"    `peer_group:` `{peer_group_status}`\n"
        f"    `dc_id:` `{dc_id}`\n"
        f"    `ping_dc:` `{ping_dc:.3f} ms`\n"
        f"    `uptime:` `{uptime_str}`"
    )

    await event.edit(output)
    
