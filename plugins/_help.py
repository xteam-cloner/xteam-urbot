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
            for d in LIST[plug]:
                x += HNDLR + d
                x += "\n"
                x += "\n© @"
        
        except BaseException as e:
            await event.eor(f"{e}")
    else:
        try:
            results = await event.client.inline_query(asst.me.username, "help")
        except BotInlineDisabledError:
            return await event.eor(get_string("help_3"))
        await results[0].click(chat.id, reply_to=event.reply_to_msg_id)
        await event.delete()


@ultroid_cmd(pattern="helpl( (.*)|$)")
async def _helper(ult):
    plug = ult.pattern_match.group(1).strip()
    chat = await ult.get_chat()
    if plug:
        try:
            x = get_string("inline_4").format(plug)
            for d in LIST[plug]:
                x += HNDLR + d
                x += "\n"
                x += "\n© @xteam_cloner"
            await ult.eor(x)
        except BaseException:
            file = None
            compare_strings = []
            for file_name in LIST:
                compare_strings.append(file_name)
                value = LIST[file_name]
                for j in value:
                    j = cmd_regex_replace(j)
                    compare_strings.append(j)
                    if j.strip() == plug:
                        file = file_name
                        break
                        if not file:
                        # the entered command/plugin name is not found
                            text = f"`{plug}` is not a valid plugin!"
                            best_match = None
                            for _ in compare_strings:
                                if plug in _ and not _.startswith("_"):
                                    best_match = _
                                    break
                                    if best_match:
                                        text += f"\nDid you mean `{best_match}`?"
                                        return await ult.eor(text)
                                        output = f"**Command** `{plug}` **found in plugin** - `{file}`\n"
                                        if file in HELP["Official"]:
                                            for i in HELP["Official"][file]:
                                                output += i
                                        elif HELP.get("Addons") and file in HELP["Addons"]:
                                            for i in HELP["Addons"][file]:
                                                output += i
                                        elif HELP.get("VCBot") and file in HELP["VCBot"]:
                                            for i in HELP["VCBot"][file]:
                                                output += i
                                                output += "\n© @xteam_cloner"
                                                await ult.eor(output)
                                                await ult.eor(x)
        except BaseException as e:
            await ult.eor(f"{e}")
        else:
            try:
                results = await ult.client.inline_query(asst.me.username, "help")
            except BotInlineDisabledError:
                return await ult.eor(get_string("help_3"))
                await results[0].click(chat.id, reply_to=ult.reply_to_msg_id)
                await ult.delete()
