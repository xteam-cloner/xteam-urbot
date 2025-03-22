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
        try:
            results = await ult.client.inline_query(asst.me.username, "ultd")
            await results[0].click(chat.id, reply_to=ult.reply_to_msg_id, hide_via=True)
            await ult.delete()
        except Exception as e:
            LOGS.info(e)
            # Count total commands
            cmd_count = sum(len(cmds) for cmds in LIST.values())
            
            # Create the help menu with clean buttons
            text = "**Help Modules**\n"
            text += f"**Prefixes:** {HNDLR}\n"
            text += f"**Commands:** {cmd_count}"
            
            buttons = [
                [
                    Button.inline("Admin", data="hlp_admin"),
                    Button.inline("Asupan", data="hlp_asupan")
                ],
                [
                    Button.inline("Auto Broadcast", data="hlp_autobc"),
                    Button.inline("Blacklist", data="hlp_blacklist")
                ],
                [
                    Button.inline("Convert", data="hlp_convert"),
                    Button.inline("Copy", data="hlp_copy")
                ],
                [
                    Button.inline("«", data="hlp_prev"),
                    Button.inline("»", data="hlp_next")
                ]
            ]
            await ult.eor(text, buttons=buttons)

@callback(pattern="hlp_(.*)")
async def help_callback(event):
    data = event.data_match.group(1).decode("utf-8")
    if data == "prev":
        await event.answer("Previous page")
    elif data == "next":
        await event.answer("Next page")
    elif data == "back":
        cmd_count = sum(len(cmds) for cmds in LIST.values())
        text = "**Help Modules**\n"
        text += f"**Prefixes:** {HNDLR}\n"
        text += f"**Commands:** {cmd_count}"
        
        buttons = [
            [
                Button.inline("Admin", data="hlp_admin"),
                Button.inline("Asupan", data="hlp_asupan")
            ],
            [
                Button.inline("Auto Broadcast", data="hlp_autobc"),
                Button.inline("Blacklist", data="hlp_blacklist")
            ],
            [
                Button.inline("Convert", data="hlp_convert"),
                Button.inline("Copy", data="hlp_copy")
            ],
            [
                Button.inline("«", data="hlp_prev"),
                Button.inline("»", data="hlp_next")
            ]
        ]
        await event.edit(text, buttons=buttons)
    else:
        # Show help for specific plugin
        try:
            output = f"**Plugin** - `{data}`\n"
            if data in HELP["Official"]:
                for i in HELP["Official"][data]:
                    output += i
            output += "\n© @xteam_cloner"
            await event.edit(output, buttons=[[Button.inline("« Back", data="hlp_back")]])
        except Exception as e:
            await event.edit(f"No help available for {data}")
