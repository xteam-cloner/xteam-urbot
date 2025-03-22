import base64
import inspect
from datetime import datetime
from html import unescape
from random import choice
from re import compile as re_compile
import re
import time
from datetime import datetime
from os import remove

from git import Repo
from telethon import Button
from telethon.tl.types import InputWebDocument, Message
from telethon.utils import resolve_bot_file_id

from pyUltroid._misc._assistant import callback, in_pattern
from pyUltroid.dB._core import HELP, LIST
from pyUltroid.fns.helper import gen_chlog, time_formatter, updater
from pyUltroid.fns.misc import split_list

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
from telethon import Button
from telethon.errors.rpcerrorlist import (
    BotMethodInvalidError,
    BotResponseTimeoutError,
    BotInlineDisabledError,
)
from pyUltroid.dB._core import HELP
from . import OWNER_NAME, ultroid_cmd, get_string


_main_help_menu = [[Button.inline("ᴍᴏᴅᴜʟᴇꜱ", data="uh_Official_")]]


@ultroid_cmd(pattern="helper$")
@in_pattern("help", owner=False)
async def inline_handler(event):
    key = "Official"
    count = 0
    text = _strings.get(key, "").format(OWNER_NAME, HNDLR, len(HELP.get(key)))

    result = await event.builder.article(
        title="alive", text=text, buttons=page_num(count, key)
    )
    await event.answer([result], cache_time=0)
