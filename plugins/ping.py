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
from telethon import events, TelegramClient
from telethon.tl.functions import PingRequest
from secrets import choice
from telethon import Button
from pyUltroid._misc import sudoers
from telethon.tl.types import InputMessagesFilterVideo, InputMessagesFilterVoice
from telethon.tl.types import InputMessagesFilterPhotos
from pyUltroid.fns.custom_markdown import CustomMarkdown
from pyUltroid.fns.helper import download_file, inline_mention
from ._inline import *
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

PING = [
    [  # First row of buttons (you can have multiple rows)
            #InlineKeyboardButton("Button 1 Text", url="https://example.com/1"),  # Example URL button
            Button.inline("CLOSE", data="close"),
        #InlineKeyboardButton("ᴘɪɴɢ", callback_data="close") # Example callback button
        ]
]

#markup = ReplyInlineMarkup(PING)



async def mention_user(user_id):
    try:
        user_entity = await ultroid_bot.get_entity(user_id)
        first_name = user_entity.first_name
        mention_text = f"[{first_name}](tg://user?id={user_id})"
        return mention_text
    except Exception as e:
        print(f"Failed to mention user: {e}")


@xteam_cmd(pattern="xping$", chats=[], type=["official", "assistant"])
async def _(event):
    start = time.time()
    x = await event.edit("ping")
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
"""@xteam_cmd(pattern="Cping")
async def wping(e):
    asupannya = [
        asupan
        async for asupan in e.client.iter_messages(
            "@xcryasupan", filter=InputMessagesFilterVideo
        )
    ]
    start = time.time()
    x = await e.eor("Pong!")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    #await asyncio.sleep(1)
    try:
       await asst.send_message(
    e.chat.id,
    f"<blockquote> Ping : {end}ms\nUptime : {uptime}\nOwner : `{inline_mention(ultroid_bot.me)}`</blockquote>",
           file=choice(asupannya),
           buttons=[
               [
                   Button.inline("• x🥰x •", data="close")
               ]
           ],
           parse_mode="html",
       )
   
except Exception as e:
      await x.edit(f"**Ping Error:** {e}")
"""
@xteam_cmd(pattern="ping$", chats=[], type=["official", "assistant"])
async def _(event):
    start = time.time()
    x = await event.reply("Ping")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    await x.edit(f"<blockquote>Pong !! {end}ms\nUptime - {uptime}</blockquote>", parse_mode="html")
    
import time
import asyncio
from telethon import Button
from telethon.tl.types import InputMessagesFilterVideo
import random

# Assuming you have these defined elsewhere in your code:
# @xteam_cmd, e, client, start_time, time_formatter, OWNER_NAME

@xteam_cmd(pattern="kping")
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
        end = round((time.time() - start) * 1000)
        uptime = time_formatter((time.time() - start_time) * 1000)

        await e.client.send_file( # send_file is used for sending files with caption and buttons.
            e.chat.id,
            file=random.choice(asupannya),
            caption=f"<blockquote> Ping : {end}ms\nUptime : {uptime}\nOwner :{OWNER_NAME}</blockquote>",
            parse_mode="html",
            buttons=Button.inline("• x •", "close"),
        )

        await x.delete() # delete the "pong" message after sending the video with caption.

    except Exception as ex:
        try:
            await x.edit(f"**Ping Error:** {ex}")
        except:
             await e.respond(f"**Ping Error:** {ex}") #in case x was not defined.

@callback(data="close", owner=True)
async def on_plug_in_callback_query_handler(event):
    await event.edit(
        get_string("inline_5"),
        buttons=Button.inline("OPEN", data="open"),
    )
