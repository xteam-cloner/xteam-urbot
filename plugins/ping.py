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
from telethon import events
from telethon.tl.functions import PingRequest
from secrets import choice
from telethon.tl.types import InputMessagesFilterVideo, InputMessagesFilterVoice
from telethon.tl.types import InputMessagesFilterPhotos
from pyUltroid.fns.custom_markdown import CustomMarkdown
from . import (
OWNER_NAME,
OWNER_ID,
start_time,
time_formatter,
udB,
ultroid_cmd as xteam_cmd,
get_string,
ultroid_bot,
eor,
)

async def mention_user(user_id):
    try:
        user_entity = await ultroid_bot.get_entity(user_id)
        first_name = user_entity.first_name
        mention_text = f"[{first_name}](tg://user?id={user_id})"
        return mention_text
    except Exception as e:
        print(f"Failed to mention user: {e}")


@xteam_cmd(pattern="ping$", chats=[], type=["official", "assistant"])
async def _(event):
    start = time.time()
    x = await event.reply("Ping!")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    await x.edit(f"**Pong!\n{end}ms**")


"""
papnya = [
        pap
        async for pap in e.client.iter_messages(
            "@CeweLogoPack", filter=InputMessagesFilterPhotos
        )
    ]

ppcpnya = [
        ppcp
        async for ppcp in event.client.iter_messages(
            "@ppcpcilik", filter=InputMessagesFilterPhotos
        )
    ]

desahcewe = [
        desah
        async for desah in event.client.iter_messages(
            "@desahancewesangesange", filter=InputMessagesFilterVoice
        )
    ]
"""
@ultroid_cmd(pattern="Cping")
async def wping(e):
    asupannya = [
        asupan
        async for asupan in e.client.iter_messages(
            "@xcryasupan", filter=InputMessagesFilterVideo
        )
    ]
    start = time.time()
    x = await e.reply("Pong!")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    #await asyncio.sleep(1)
    try:
        await x.edit(get_string("ping").format(end, uptime, f"{OWNER_NAME}"), file=choice(asupannya))
        #await x.edit(f"**Ping :** `{end}ms`\n**Uptime :** `{uptime}`\n**Owner** :`{OWNER_NAME}`", file=choice(asupannya))
    except Exception as e:
        await x.edit(f"**Ping Error:** {e}")
