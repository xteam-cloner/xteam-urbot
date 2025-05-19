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
async def _help(ult):
    plug = ult.pattern_match.group(1).strip()
    chat = await ult.get_chat()
    try:
        if plug:
            try:
                x = get_string("help_11").format(plug)
                for d in LIST[plug]:
                    x += HNDLR + d
                    x += "\n"
                x += "\n© @xteam_cloner"
                await ult.eor(x)
            except KeyError:
                file = None
                compare_strings = []
                for file_name, value in LIST.items():
                    compare_strings.append(file_name)
                    for j in value:
                        j = cmd_regex_replace(j)
                        compare_strings.append(j)
                        if j.strip() == plug:
                            file = file_name
                            break
                    if file:
                        break
                if not file:
                    text = f"`{plug}` is not a valid plugin!"
                    best_match = next(
                        (
                            _
                            for _ in compare_strings
                            if plug in _ and not _.startswith("_")
                        ),
                        None,
                    )
                    if best_match:
                        text += f"\nDid you mean `{best_match}`?"
                    return await ult.eor(text)
                output = f"**Command** `{plug}` **found in plugin** - `{file}`\n"
                if file in HELP.get("Official", {}):
                    output += "".join(HELP["Official"][file])
                elif file in HELP.get("Addons", {}):
                    output += "".join(HELP["Addons"][file])
                elif file in HELP.get("VCBot", {}):
                    output += "".join(HELP["VCBot"][file])
                output += "\n© @xteam_cloner"
                await ult.eor(output)
        else:
            try:
                results = await ult.client.inline_query(asst.me.username, "help")
                await results[0].click(
                    chat.id, reply_to=ult.reply_to_msg_id, hide_via=True
                )
                await ult.delete()
            except BotMethodInvalidError:
                all_commands = [cmd for cmds in LIST.values() for cmd in cmds]
                total_commands = len(all_commands) + 10
                buttons = list(_main_help_menu)
                if udB.get_key("MANAGER") and udB.get_key("DUAL_HNDLR") == "/":
                    buttons.insert(2, [Button.inline("• Manager Help •", "mngbtn")])
                await ult.reply(
                    get_string("inline_4").format(
                        OWNER_NAME,
                        len(HELP.get("Official", {})),
                        len(HELP.get("Addons", {})),
                        total_commands,
                    ),
                    file=inline_pic(),
                    buttons=buttons,
                )
            except (BotResponseTimeoutError, BotInlineDisabledError) as e:
                error_message = (
                    get_string("help_2").format(HNDLR)
                    if isinstance(e, BotResponseTimeoutError)
                    else get_string("help_3")
                )
                return await ult.eor(error_message)
    except Exception as er:
        LOGS.exception(er)
        await ult.eor("Error 🤔 occurred.")
