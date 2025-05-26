# UserBot
# Copyright (C) 2021-2023 Teamx-cloner
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

from . import get_help

__doc__ = get_help("help_bot")

import asyncio
import os
import sys
import time
import random
from telethon.errors import FloodWaitError
from telethon import Button
from telethon import events, TelegramClient
from telethon.tl.functions import PingRequest
from secrets import choice
from telethon.tl.types import (
    InputMessagesFilterVideo,
    InputMessagesFilterVoice,
    InputMessagesFilterPhotos,
)
from xteam._misc import sudoers
from xteam.fns.custom_markdown import CustomMarkdown
from xteam.fns.helper import download_file, inline_mention
from ._inline import *
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

PING = [
    [  # First row of buttons (you can have multiple rows)
        Button.inline("CLOSE", data="close"),
    ]
]

# markup = ReplyInlineMarkup(PING)


async def mention_user(user_id):
    try:
        user_entity = await ultroid_bot.get_entity(user_id)
        first_name = user_entity.first_name
        mention_text = f"[{first_name}](tg://user?id={user_id})"
        return mention_text
    except Exception as e:
        print(f"Failed to mention user: {e}")


@xteam_cmd(pattern="Cping$", chats=[], type=["official", "assistant"])
async def _(event):
    start = time.time()
    x = await event.edit("ping")
    end = round((time.time() - start) * 1000)  # Corrected to milliseconds
    uptime = time_formatter((time.time() - start_time) * 1000)  # Corrected to milliseconds
    await x.edit(f"Pong !! {end}ms\nUptime - {uptime}")

@xteam_cmd(pattern="ping$", chats=[], type=["official", "assistant"])
async def _(event):
    start = time.time()
    x = await event.reply("Ping")
    end = round((time.time() - start) * 1000)  # Corrected to milliseconds
    uptime = time_formatter((time.time() - start_time) * 1000)  # Corrected to milliseconds
    await x.edit(f"<blockquote>Pong !! {end}ms\nUptime - {uptime}</blockquote>", parse_mode="html")


@xteam_cmd(pattern="Aping")
async def wping(e):
    try:
        asupannya = [
            asupan
            async for asupan in e.client.iter_messages(
                "@xcryasupan", filter=InputMessagesFilterVideo
            )
        ]

        if not asupannya:
            await e.respond("No video found in @xcryasupan.")
            return

        start = time.time()
        x = await e.eor("Pong!")  # Use respond instead of eor for initial message
        end = round((time.time() - start) * 1000)  # Corrected to milliseconds
        uptime = time_formatter((time.time() - start_time) * 1000)  # Corrected to milliseconds

        await e.client.send_file(  # send_file is used for sending files with caption and buttons.
            e.chat.id,
            file=random.choice(asupannya),
            caption=f"<blockquote> Ping : {end}ms\nUptime : {uptime}\nOwner :{OWNER_NAME}</blockquote>",
            parse_mode="html",
            buttons=Button.inline("• x •", "close"),
        )

        await x.delete()  # delete the "pong" message after sending the video with caption.

    except Exception as ex:
        try:
            await x.edit(f"**Ping Error:** {ex}")
        except:
            await e.respond(f"**Ping Error:** {ex}")  # in case x was not defined.


@callback(data="close", owner=True)
async def on_plug_in_callback_query_handler(event):
    await event.edit(
        get_string("inline_5"),
        buttons=Button.inline("OPEN", data="open"),
    )


async def detect_flood_wait(module_name, func, *args, **kwargs):
    """
    Mendeteksi apakah sebuah fungsi menyebabkan FloodWaitError.

    Args:
        module_name (str): Nama modul atau fungsi yang dipanggil.
        func (callable): Fungsi yang akan dijalankan.
        *args: Argumen posisi untuk fungsi.
        **kwargs: Argumen kata kunci untuk fungsi.

    Returns:
        Tuple[Any, Optional[int]]: Hasil dari fungsi dan durasi flood wait (jika terjadi), atau (None, None).
    """
    try:
        result = await func(*args, **kwargs)
        return result, None
    except FloodWaitError as e:
        print(f"Terdeteksi Flood Wait pada modul '{module_name}' selama {e.seconds} detik.")
        return None, e.seconds
    except Exception as e:
        print(f"Terjadi error lain pada modul '{module_name}': {e}")
        return None, None


@xteam_cmd(pattern="Ping$", chats=[], type=["official", "assistant"])
async def _(event):
    start = time.time()
    ping_result, flood_wait_time = await detect_flood_wait("Balas Pesan (Ping)", event.reply, "Ping")
    end = round((time.time() - start) * 1000)  # Corrected to milliseconds
    uptime = time_formatter((time.time() - start_time) * 1000)  # Corrected to milliseconds

    message = f"<blockquote>Pong !! {end}ms\nUptime - {uptime}</blockquote>"
    if flood_wait_time:
        message += f"\n\n⚠️ Terdeteksi Flood Wait selama {flood_wait_time} detik saat membalas pesan."

    await event.edit(message, parse_mode="html")

# Pastikan dekorator @xteam_cmd dan definisi fungsi _ berada dalam scope yang benar.

# UserBot
# Copyright (C) 2021-2023 Teamx-cloner
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

import asyncio
import os
import sys
import time
import random
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
# from secrets import choice # Not directly used in the provided snippet
# from pyrogram.raw.types import InputMessagesFilterVideo, InputMessagesFilterVoice, InputMessagesFilterPhotos # Pyrogram handles this differently

# Asumsi Anda memiliki fungsi-fungsi ini di tempat lain atau perlu diimplementasikan
# from xteam._misc import sudoers
# from xteam.fns.custom_markdown import CustomMarkdown
# from xteam.fns.helper import download_file, inline_mention
# from ._inline import * # Asumsi ini dihandle oleh Pyrogram's filters and handlers
# from xteam.fns.helper import inline_mention
# from . import (
#     OWNER_NAME,
#     OWNER_ID,
#     BOT_NAME,
#     OWNER_USERNAME,
#     asst,
#     start_time,
#     time_formatter,
#     udB,
#     ultroid_cmd as xteam_cmd,
#     get_string,
#     ultroid_bot as client,
#     eor,
#     ultroid_bot,
#     call_back,
#     callback,
# )
from xteam.startup.BaseClient import PyrogramClient # Ini sudah diimpor sebagai Client dari pyrogram

# Fungsi dummy untuk contoh, ganti dengan implementasi Anda yang sebenarnya
def time_formatter(milliseconds: int) -> str:
    seconds = int(milliseconds / 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d ") if days else "")
        + ((str(hours) + "h ") if hours else "")
        + ((str(minutes) + "m ") if minutes else "")
        + ((str(seconds) + "s ") if seconds else "")
    )
    return tmp if tmp else "0s"

# Asumsi Anda punya instance Client yang diinisialisasi
# contoh:
# app = Client(
#     "my_account",
#     api_id=YOUR_API_ID,
#     api_hash=YOUR_API_HASH,
#     bot_token=YOUR_BOT_TOKEN # Jika ini adalah bot, bukan userbot murni
# )

# Ganti dengan instance Pyrogram Client Anda
# Misalnya, jika Anda menginisialisasi client Anda sebagai `app`
# app = Client("my_userbot", api_id=YOUR_ID, api_hash=YOUR_HASH)
# Anda mungkin perlu menyesuaikan `client` dengan nama variabel instance Pyrogram Anda
# Misalnya, jika Anda menggunakan `app`, ganti `client` menjadi `app` di decorator dan fungsi.
#client = Client("my_userbot", api_id=12345, api_hash="your_api_hash_here") # Ganti dengan kredensial Anda

# --- Perubahan utama untuk Pyrogram ---
# Dekorator Pyrogram menggunakan filters.command dan filters.me (untuk userbot)

@PyrogramClient.on_message(filters.command("Cpung", prefixes=".") & filters.me)
async def cping_command(client, message):
    """
    Handles the .Cping command for Pyrogram.
    """
    start = time.time()
    # Pyrogram menggunakan message.edit_text untuk mengedit pesan
    x = await message.edit_text("`Ping...`")
    end = round((time.time() - start) * 1000)  # dalam milidetik
    uptime_ms = (time.time() - start_time) * 1000
    uptime = time_formatter(uptime_ms)
    await x.edit_text(f"**Pong!** `{end}ms`\n**Uptime:** `{uptime}`")

# Untuk menjalankan bot (opsional, tergantung bagaimana Anda mengatur startup)
# if __name__ == "__main__":
#     print("Starting Pyrogram client...")
#     client.run()
