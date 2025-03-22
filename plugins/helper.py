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
from pyUltroid.dB._core import HELP, LIST
from pyUltroid.fns.tools import cmd_regex_replace

from . import HNDLR, LOGS, OWNER_NAME, asst, get_string, inline_pic, udB, ultroid_cmd, call_back, callback, def_logs, eor, get_string, heroku_logs, in_pattern

_main_help_menu = [
    [
        Button.inline("ᴍᴏᴅᴜʟᴇꜱ", data="uh_Official_"),
    ],
    [Button.inline("ᴄʟᴏꜱᴇ", data="close")],
]

@ultroid_cmd(pattern="help( (.*)|$)")
async def _help(ult):
    plug = ult.pattern_match.group(1).strip()
    chat = await ult.get_chat()
    if plug:
        try:
            if plug in HELP["Official"]:
                output = f"**Plugin** - `{plug}`\n"
                for i in HELP["Official"][plug]:
                    output += i
                output += "\n© @xteam_cloner"
                await ult.eor(output)
            elif HELP.get("Addons") and plug in HELP["Addons"]:
                output = f"**Plugin** - `{plug}`\n"
                for i in HELP["Addons"][plug]:
                    output += i
                output += "\n© @xteam_cloner"
                await ult.eor(output)
            elif HELP.get("VCBot") and plug in HELP["VCBot"]:
                output = f"**Plugin** - `{plug}`\n"
                for i in HELP["VCBot"][plug]:
                    output += i
                output += "\n© @xteam_cloner"
                await ult.eor(output)
            else:
                try:
                    x = get_string("help_11").format(plug)
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
                    output += "\n© @xteam_cloner"
                    await ult.eor(output)
        except BaseException as er:
            LOGS.exception(er)
            await ult.eor("Error 🤔 occurred.")
    else:
        help_menu = [
            [Button.inline("ᴀᴅᴍɪɴ", data="help_admin"),
             Button.inline("ᴀᴅᴢᴀɴ", data="help_adzan")],
            [Button.inline("ᴀꜰᴋ", data="help_afk"),
             Button.inline("ʙʟᴀᴄᴋʟɪꜱᴛ", data="help_blacklist")],
            [Button.inline("ʙᴜᴛᴛᴏɴ", data="help_button"),
             Button.inline("ᴄʜᴀᴛʙᴏx", data="help_chatbox")],
            [Button.inline("ᴄᴏɴᴠᴇʀᴛ", data="help_convert"),
             Button.inline("ᴄᴏᴘʏ", data="help_copy")],
            [Button.inline("ꜰᴏɴᴛ", data="help_font"),
             Button.inline("ɢᴄᴀꜱᴛ", data="help_gcast")],
            [Button.inline("◀️", data="help_prev"),
             Button.inline("▶️", data="help_next")]
        ]
        await ult.eor("**JIYO VX | UB**", buttons=help_menu)

@callback(pattern="help_(.*)")
async def help_callback(event):
    plugin = event.data_match.group(1).decode("utf-8")
    if plugin == "prev":
        # Handle previous page
        await event.edit("Previous page", buttons=help_menu)  # You'll need to define previous page buttons
    elif plugin == "next":
        # Handle next page
        await event.edit("Next page", buttons=help_menu)  # You'll need to define next page buttons
    else:
        # Show help for specific plugin
        try:
            output = f"**Plugin** - `{plugin}`\n"
            if plugin in HELP["Official"]:
                for i in HELP["Official"][plugin]:
                    output += i
            output += "\n© @xteam_cloner"
            await event.edit(output, buttons=[[Button.inline("« Back", data="help_back")]])
        except Exception as e:
            await event.edit(f"No help available for {plugin}")
