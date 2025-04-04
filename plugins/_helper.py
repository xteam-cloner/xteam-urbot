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
from ._inline import *
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

@ultroid_cmd(pattern="helper(.*)")
async def help_func(ult):
    key, count = ult.pattern_match.group(1).decode("utf-8").split("_")
    if key == "VCBot" and HELP.get("VCBot") is None:
        return await ult.answer(get_string("help_12"), alert=True)
    elif key == "Addons" and HELP.get("Addons") is None:
        return await ult.answer(get_string("help_13").format(HNDLR), alert=True)
    if "|" in count:
        _, count = count.split("|")
    count = int(count) if count else 0
    text = _strings.get(key, "").format(OWNER_NAME, len(HELP.get(key)))
    await ult.edit(text, buttons=page_num(count, key), link_preview=False)
else:
try:
    results = await ult.client.inline_query(asst.me.username, text, buttons=page_num(count, key), link_preview=False))
except BotMethodInvalidError:
    return await ult.reply(
        "Inline mode is disabled. Please enable it in bot settings or contact support.",
    )
except BotResponseTimeoutError:
    return await ult.eor(
        "The bot did not respond in time. Please try again later.",
    )
"""except BotInlineDisabledError:
    return await ult.eor("The bot's inline mode is currently disabled.")
    await results[0].click(chat.id, reply_to=ult.reply_to_msg_id, hide_via=True)
    await ult.delete()"""
