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

import re
from telethon import events, Button, custom

HELP = {}  # Assuming you have a dictionary like this

@ultroid_cmd(pattern="helper( (.*)|$)")
async def help_cmd(event):
    module = event.pattern_match.group(1).strip()
    if module in HELP:
        await event.respond(HELP[module].__HELP__, parse_mode='html')
    else:
        await event.respond(f"<b>No Module Named <code>{module}</code></b>", parse_mode='html')
    await event.respond(
        "<b>Command & Help</b>",
        buttons=paginate_modules(0, HELP, "help"),
        parse_mode='html'
    )

def paginate_modules(page_number, module_dict, prefix):
    modules = sorted(list(module_dict.keys()))
    chunked_modules = [modules[i:i + 8] for i in range(0, len(modules), 8)]
    if page_number == len(chunked_modules):
        page_number = 0
    elif page_number < 0:
        page_number = len(chunked_modules) - 1
    buttons = []
    for module in chunked_modules[page_number]:
        buttons.append(Button.inline(module.replace('_', ' '), data=f"help_module({module})"))
    nav_buttons = []
    if len(chunked_modules) > 1:
        nav_buttons.append(Button.inline("<", data=f"help_prev({page_number - 1})"))
        nav_buttons.append(Button.inline(">", data=f"help_next({page_number + 1})"))
    if nav_buttons:
        buttons.append(nav_buttons)
    return buttons

async def menu_callback(event):
    data = event.data.decode()
    mod_match = re.match(rb"help_module\((.+?)\)", event.data)
    prev_match = re.match(rb"help_prev\((.+?)\)", event.data)
    next_match = re.match(rb"help_next\((.+?)\)", event.data)
    back_match = re.match(rb"help_back", event.data)
    top_text = "<b>Command & Help</b>"

    if mod_match:
        module = mod_match.group(1).decode().replace(" ", "_")
        text = HELP[module].__HELP__
        await event.edit(text, buttons=Button.inline("Back", data=b"help_back"), parse_mode='html')
    elif prev_match:
        curr_page = int(prev_match.group(1).decode())
        await event.edit(top_text, buttons=paginate_modules(curr_page, HELP, "help"), parse_mode='html')
    elif next_match:
        next_page = int(next_match.group(1).decode())
        await event.edit(top_text, buttons=paginate_modules(next_page, HELP, "help"), parse_mode='html')
    elif back_match:
        await event.edit(top_text, buttons=paginate_modules(0, HELP, "help"), parse_mode='html')

async def nothing_here(event):
    buttons = [
        [
            Button.url("Deploy kangerBot", "https://t.me/Kangerbot?start"),
            Button.url("Update Channel", "https://t.me/Kanger"),
        ]
    ]

    await event.answer(
        [
            custom.InlineResult(
                id="1",
                type="article",
                title="About KangerBot",
                input_message=custom.InputTextMessageContent(
                    """
👾<b>KangerBot</b>

Simple userbot telegram based in telethon.
• Send messages to all groups/users simultaneously
• Set a scheduled/reminder message
• Manage and moderate the group
• Respond to orders
...And many more!
""",
                    parse_mode='html'
                ),
                description="Click this to see",
                url="https://t.me/Kangerbot",
                thumb= "https://telegra.ph//file/3838aa50510fd5020c2b3.jpg",
                buttons=buttons,
            )
        ]
    )

# Register the handlers
async def setup_handlers(client):
    client.add_event_handler(help_cmd, events.NewMessage(pattern=r"(?i)^\.helper(?: |$)(.*)"))
    client.add_event_handler(menu_callback, events.CallbackQuery(pattern=re.compile(rb"help_")))
    client.add_event_handler(nothing_here, events.InlineQuery(pattern=r"user_help"))

# Example of how to add a help command
# HELP["example"] = type('HelpCommand', (), {"__HELP__": "This is an example help command."})
