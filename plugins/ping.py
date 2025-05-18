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
    end = round((time.time() - start) * 100)  # Corrected to milliseconds
    uptime = time_formatter((time.time() - start_time) * 100)  # Corrected to milliseconds
    await x.edit(f"Pong !! {end}ms\nUptime - {uptime}")

@xteam_cmd(pattern="ping$", chats=[], type=["official", "assistant"])
async def _(event):
    start = time.time()
    x = await event.reply("Ping")
    end = round((time.time() - start) * 100)  # Corrected to milliseconds
    uptime = time_formatter((time.time() - start_time) * 100)  # Corrected to milliseconds
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
        x = await e.respond("Pong!")  # Use respond instead of eor for initial message
        end = round((time.time() - start) * 100)  # Corrected to milliseconds
        uptime = time_formatter((time.time() - start_time) * 100)  # Corrected to milliseconds

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
    end = round((time.time() - start) * 100)  # Corrected to milliseconds
    uptime = time_formatter((time.time() - start_time) * 100)  # Corrected to milliseconds

    message = f"<blockquote>Pong !! {end}ms\nUptime - {uptime}</blockquote>"
    if flood_wait_time:
        message += f"\n\n⚠️ Terdeteksi Flood Wait selama {flood_wait_time} detik saat membalas pesan."

    await event.edit(message, parse_mode="html")

# Pastikan dekorator @xteam_cmd dan definisi fungsi _ berada dalam scope yang benar.
