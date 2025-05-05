import re
import time
from datetime import datetime
from os import remove
import resources
from git import Repo
from telethon import Button
from telethon.tl.types import InputWebDocument, Message
from telethon.utils import resolve_bot_file_id

from xteam._misc._assistant import callback, in_pattern
from xteam.dB._core import HELP, LIST
from xteam.fns.helper import gen_chlog, time_formatter, updater
from xteam.fns.misc import split_list

from . import (
    HNDLR,
    LOGS,
    OWNER_NAME,
    InlinePlugin,
    asst,
    get_string,
    inline_pic,
    split_list,
    start_time,
    udB,
)
from ._help import _main_help_menu

from random import choice
from telethon.tl.types import InputMessagesFilterVideo
from telethon import events, Button

@in_pattern("asupan", owner=True)
async def asupan_handler(event):
    xx = await event.reply("Mencari asupan...")
    try:
        asupannya = [
            asupan
            async for asupan in event.client.iter_messages(
                "@xcryasupan", filter=InputMessagesFilterVideo
            )
        ]
        video = choice(asupannya)
        buttons = [[Button.inline("Asupan Lain?", data="next_asupan")]]
        await event.client.send_file(
            event.chat_id,
            file=video,
            caption=f"Asupan BY 🥀{OWNER_NAME}🥀",
            reply_to=event.reply_to_msg_id,
            buttons=buttons,
        )
        await xx.delete()
    except Exception:
        await xx.edit("**Tidak bisa menemukan video asupan.**")

@callback("next_asupan", owner=True)
async def next_asupan_handler(event):
    try:
        asupannya = [
            asupan
            async for asupan in event.client.iter_messages(
                "@xcryasupan", filter=InputMessagesFilterVideo
            )
        ]
        video = choice(asupannya)
        await event.client.send_file(
            event.chat_id,
            file=video,
            caption=f"Asupan BY 🥀{OWNER_NAME}🥀",
            reply_to=event.reply_to_msg_id,
        )
        await event.answer("Asupan baru!")
    except Exception:
        await event.answer("Tidak bisa menemukan video asupan lain.")
