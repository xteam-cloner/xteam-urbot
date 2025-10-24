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
    ultroid_bot,
    eor,
    ultroid_bot,
    call_back,
    callback,
)


async def mention_user(user_id):
    try:
        user_entity = await ultroid_bot.get_entity(user_id)
        first_name = user_entity.first_name
        mention_text = f"[{first_name}](tg://user?id={user_id})"
        return mention_text
    except Exception as e:
        print(f"Failed to mention user: {e}")


@xteam_cmd(pattern="ping(|x|s)$", chats=[], type=["official", "assistant"])
async def _(event):
    ultroid_bot.parse_mode = CustomMarkdown()
    user_id = OWNER_ID
    ment = await mention_user(user_id)
    bot_header = f"<b>Mʏꜱᴛᴇʀɪᴏᴜꜱ Gɪʀʟꜱ</b>"
    prem = event.pattern_match.group(1)
    start = time.time()
    x = await event.reply("ping")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    if prem == "x":
        await x.reply(get_string("pping").format(end, uptime))
    elif prem == "s":
        await x.reply(get_string("iping").format(end))
    else:
        pic = udB.get_key("PING_PIC")
        await asyncio.sleep(1)
        await x.edit(get_string("ping").format(bot_header, end, uptime, f"{OWNER_NAME}"), file=pic)
    

@xteam_cmd(pattern="Ping$", chats=[], type=["official", "assistant"])
async def _(event):
    ultroid_bot.parse_mode = CustomMarkdown()
    user_id = OWNER_ID
    ment = await mention_user(user_id)
    start = time.time()
    x = await event.reply("Ping")
    end = round((time.time() - start) * 1000)  # Corrected to milliseconds
    uptime = time_formatter((time.time() - start_time) * 1000)  # Corrected to milliseconds
    await x.reply(get_string("pping").format(end, uptime, OWNER_NAME))
    #await x.edit(f"🏓 Pong • {end}ms\n⏰ Uptime • {uptime}\n👑 Owner • {OWNER_NAME}")

