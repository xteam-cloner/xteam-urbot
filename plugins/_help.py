# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

import base64
import inspect
from datetime import datetime
from html import unescape
from random import choice
from re import compile as re_compile

from bs4 import BeautifulSoup as bs
from telethon import Button
from telethon.tl.alltlobjects import LAYER, tlobjects
from telethon.tl.types import DocumentAttributeAudio as Audio
from telethon.tl.types import InputWebDocument as wb

from telethon.errors.rpcerrorlist import (
    BotInlineDisabledError,
    BotMethodInvalidError,
    BotResponseTimeoutError,
)
from telethon.tl.custom import Button
from assistant import *
from xteam.dB._core import HELP, LIST
from xteam.fns.tools import cmd_regex_replace

from . import HNDLR, LOGS, OWNER_NAME, asst, get_string, inline_pic, udB, ultroid_cmd, call_back, callback, def_logs, eor, get_string, heroku_logs, in_pattern

_main_help_menu = [
    [
        Button.inline("🏡 Modules 🏡", data="uh_Official_"),
    ],
    
    ]


@ultroid_cmd(pattern="help( (.*)|$)")
async def _help(event):
    plug = event.pattern_match.group(1).strip()
    chat = await event.get_chat()
    if plug:
        try:
            x = get_string("help_11").format(plug)
            if plug in HELP["Official"]:
                output = f"Plugin - {plug}\n"
                for i in HELP["Official"][plug]:
                    output += i
                output += "\n© @TeamUltroid"
                await ult.eor(output)
            elif HELP.get("Addons") and plug in HELP["Addons"]:
                output = f"Plugin - {plug}\n"
                for i in HELP["Addons"][plug]:
                    output += i
                output += "\n© @TeamUltroid"
                await ult.eor(output)
            elif HELP.get("VCBot") and plug in HELP["VCBot"]:
                output = f"Plugin - {plug}\n"
                for i in HELP["VCBot"][plug]:
                    output += i
                output += "\n© @TeamUltroid"
                await ult.eor(output)
        except BaseException as e:
            await event.eor(f"{e}")
        else:
            try:
                results = await event.client.inline_query(asst.me.username, "help")
            except BotInlineDisabledError:
                return await event.eor(get_string("help_3"))
                await results[0].click(chat.id, reply_to=event.reply_to_msg_id)
                await event.delete()
