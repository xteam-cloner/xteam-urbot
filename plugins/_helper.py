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


from telethon import Button, events
from telethon.tl.alltlobjects import LAYER, tlobjects
from telethon.tl.types import (
    DocumentAttributeAudio as Audio,
    InputWebDocument as wb,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from telethon.errors.rpcerrorlist import (
    BotInlineDisabledError,
    BotMethodInvalidError,
    BotResponseTimeoutError,
)
from telethon.tl.custom import Button

# Assuming you have these defined elsewhere in your project
# Replace with your actual definitions
HNDLR = "."  # Example handler
LOGS = print  # Example logging function
OWNER_NAME = "Owner"  # Example owner name
asst = None  # Example assistant client
udB = None  # Example database
bot = None  # telethon bot instance
prefix = ["."]  # example prefix
LIST = {}  # example help dict
get_arg = lambda message: message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
get_prefix = lambda user_id: prefix  # example prefix retrieval function

# Example functions (replace with your actual implementations)
async def eor(message, text):
    await message.edit(text)


# Example function for pagination
def paginate_modules(page_number, module_dict, prefix):
    modules = sorted(
        [(key, value) for key, value in module_dict.items() if key != "start" and key != "help"]
    )
    chunked_modules = [modules[i : i + 9] for i in range(0, len(modules), 9)]
    if len(chunked_modules) == 0:
        return [[Button.inline("Back", callback_data="help_back")]]
    current_page = chunked_modules[page_number]
    buttons = [
        [
            Button.inline(
                text=module_name.replace("_", " ").title(),
                callback_data=f"help_module({module_name})",
            )
        ]
        for module_name, module in current_page
    ]
    if len(chunked_modules) > 1:
        nav_buttons = []
        if page_number > 0:
            nav_buttons.append(
                Button.inline(
                    text="<", callback_data=f"help_prev({page_number - 1})"
                )
            )
        if page_number < len(chunked_modules) - 1:
            nav_buttons.append(
                Button.inline(
                    text=">", callback_data=f"help_next({page_number + 1})"
                )
            )
        if nav_buttons:
            buttons.append(nav_buttons)
    return buttons


async def help_cmd(client, message):
    if not get_arg(message):
        try:
            x = await client.get_inline_bot_results(bot.me.username, "help")
            await message.reply(file=x.results[0].document)
        except Exception as error:
            await message.reply(str(error))
    else:
        nama = get_arg(message)
        if get_arg(message) in LIST:
            await message.reply(
                LIST[get_arg(message)].__HELP__.format(prefix[0])
                + f"\n<b>© {bot.me.mention}</b>",
                quote=True,
                parse_mode="html",
            )
        else:
            await message.reply(f"<b>❌ Tidak ada modul bernama <code>{nama}</code></b>", parse_mode="html")


async def menu_inline(client, inline_query):
    user_id = inline_query.from_user.id
    emut = await get_prefix(user_id)
    msg = "<b>Help Modules\n     Prefixes: `{}`\n     Commands: <code>{}</code></b>".format(
        " ".join(emut), len(LIST)
    )
    await client.answer_inline_query(
        inline_query.id,
        cache_time=0,
        results=[
            (
                InlineQueryResultArticle(
                    title="Help Menu!",
                    reply_markup=Button.inline(
                        paginate_modules(0, LIST, "help")
                    ),
                    input_message_content=InputTextMessageContent(msg, parse_mode="html"),
                )
            )
        ],
    )


async def menu_callback(client, callback_query):
    mod_match = re.match(r"help_module\((.+?)\)", callback_query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", callback_query.data)
    next_match = re.match(r"help_next\((.+?)\)", callback_query.data)
    back_match = re.match(r"help_back", callback_query.data)
    user_id = callback_query.from_user.id
    prefix = await get_prefix(user_id)
    if mod_match:
        module = (mod_match.group(1)).replace(" ", "_")
        text = f"<b>{LIST[module].__HELP__}</b>\n".format(prefix[0])
        button = [[Button.inline("Kembali", callback_data="help_back")]]
        await callback_query.edit_message_text(
            text=text + f"\n<b>© {bot.me.mention}</b>",
            reply_markup=Button.inline(button),
            disable_web_page_preview=True,
            parse_mode="html",
        )
    top_text = "<b>Help Modules\n     Prefixes: <code>{}</code>\n     Commands: <code>{}</code></b>".format(
        " ".join(prefix), len(LIST)
    )

    if prev_match:
        curr_page = int(prev_match.group(1))
        await callback_query.edit_message_text(
            text=top_text,
            reply_markup=Button.inline(
                paginate_modules(curr_page - 1, LIST, "help")
            ),
            disable_web_page_preview=True,
            parse_mode="html",
        )
    if next_match:
        next_page = int(next_match.group(1))
        await callback_query.edit_message_text(
            text=top_text,
            reply_markup=Button.inline(
                paginate_modules(next_page + 1, LIST, "help")
            ),
            disable_web_page_preview=True,
            parse_mode="html",
        )
    if back_match:
        await callback_query.edit_message_text(
            text=top_text,
            reply_markup=Button.inline(
                paginate_modules(0, LIST, "help")
            ),
            disable_web_page_preview=True,
            parse_mode="html",
        )


# Example event handlers (replace with your actual event registration)
@ultroid_cmd(pattern=r"help")
async def help_handler(event):
    await help_cmd(bot, event)


@in_pattern("help", owner=True)
async def inline_help_handler(event):
    await menu_inline(bot, event)


@callback("help", owner=True)
async def callback_help_handler(event):
    await menu_callback(bot, event)
    
