import base64
import inspect
from datetime import datetime
from html import unescape
from random import choice
from re import compile as re_compile

from telethon import Button
from telethon.errors.rpcerrorlist import (
    BotMethodInvalidError,
    BotResponseTimeoutError,
    BotInlineDisabledError,
)
from pyUltroid.dB._core import HELP
from . import OWNER_NAME, ultroid_cmd, get_string

_main_help_menu = [[Button.inline("ᴍᴏᴅᴜʟᴇꜱ", data="uh_Official_")]]


@ultroid_cmd(pattern="help$")
async def _help(ult):
    try:
        await ult.reply(
            get_string("inline_4").format(
                OWNER_NAME,
                len(HELP.get("Official", [])),
                len(HELP.get("Addons", [])),
                80,  # Example: total modules count.
            ),
            buttons=_main_help_menu,
        )
    except BotInlineDisabledError:
        await ult.eor(get_string("help_3"))
        
