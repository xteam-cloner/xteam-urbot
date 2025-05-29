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

from xteam._misc import SUDO_M, owner_and_sudos
from xteam.dB.base import KeyManager
from xteam.fns.helper import inline_mention

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
    return f"<blockquote expandable><b>✰ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✰</b>\n\n" \
                     f"✵ Owner : {OWNER_NAME}\n" \
                     f"✵ Dc id : {ultroid_bot.dc_id}\n" \
                     f"✵ Library : {lver}\n" \
                     f"✵ Uptime : {uptime}\n" \
                     f"✵ Telethon : {tver}\n" \
                     f"✵ Pyrogram :  {pver}\n" \
                     f"✵ Python : {pyver()}\n</blockquote>"

@xteam_cmd(pattern="alive$")
async def alive(event):
    start = time.time()
    pro = await event.eor("🔥")
    await asyncio.sleep(1)
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    message_text = format_message_text(uptime)
    await pro.edit(f"<blockquote expandable><b>✰ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✰</b>\n\n" \
                     f"✵ Owner : {OWNER_NAME}\n" \
                     f"✵ Dc id : {ultroid_bot.dc_id}\n" \
                     f"✵ Library : {lver}\n" \
                     f"✵ Uptime : {uptime}\n" \
                     f"✵ Telethon : {tver}\n" \
                     f"✵ Pyrogram :  {pver}\n" \
                     f"✵ Python : {pyver()}\n</blockquote>",
                   parse_mode="html",
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


@xteam_cmd(pattern="live$")
async def live_video(event):
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

        # Assuming start_time and time_formatter are defined
        uptime = time_formatter((time.time() - start_time) * 1000) # Assuming time_formatter expects milliseconds
        message_text = format_message_text(uptime)

        selected_video_message = random.choice(asupannya)

        # Create the inline keyboard with a "Close" button
        buttons = [
            [Button.inline("Close", data="close_alive_message")]
        ]

        if selected_video_message.video:
            await client.send_message(
                event.chat.id,
                caption=message_text,
                parse_mode="html",
                buttons=buttons # Add the buttons here
            )
        else:
            await event.respond("Selected message does not contain a video.")

    except Exception as e:
        await event.respond(f"An error occurred: {e}")

# --- You need a handler for the 'Close' button callback ---
@callback(data="close_alive_message")
async def close_message_callback(event):
    await event.delete() # Deletes the message where the button was pressed
    await event.answer("Message closed!") # Optional: show a small notification to the user

@in_pattern("alive", owner=False)  # Mengubah dari xteam_cmd ke in_pattern
async def alive_inline_handler(ult):  # Mengganti 'event' dengan 'ult' dan nama fungsi agar lebih jelas
    start = time.time()
    # Asumsi ult.builder memiliki metode untuk membuat 'article'
    # dan kita tidak perlu melakukan 'eor' atau 'edit' secara terpisah
    # karena kita akan mengembalikan seluruh hasil dalam satu 'article'.
    # Untuk mendapatkan nilai uptime dan lainnya, kita perlu akses ke variabel global
    # seperti start_time, ultroid_bot.dc_id, lver, tver, pver, pyver()
    # yang tidak didefinisikan dalam scope ini. Saya akan mengasumsikan mereka sudah ada.

    # Menghitung uptime, dll.
    end_time_calc = time.time() # Menghitung waktu akhir untuk latency
    uptime = time_formatter((end_time_calc - start_time) * 1000)

    # Membangun teks pesan
    message_text = (
        f"<b>✰ xᴛᴇᴀᴍ ᴜʀʙᴏᴛ ɪꜱ ᴀʟɪᴠᴇ ✰</b>\n\n"
        f"✵ Owner : {OWNER_NAME}\n"
        f"✵ Dc id : {ultroid_bot.dc_id}\n"
        f"✵ Library : {lver}\n"
        f"✵ Uptime : {uptime}\n"
        f"✵ Telethon : {tver}\n"
        f"✵ Pyrogram :  {pver}\n"
        f"✵ Python : {pyver()}"
    )

    result = await ult.builder.article(
        title="Bot Status", # Judul artikel untuk hasil inline
        text=message_text,
        parse_mode="html" # Pastikan mode parse diatur jika ada HTML
    )
    await ult.answer([result], cache_time=0)
