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
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import (
    BotInlineDisabled,
    BotMethodInvalid,
    BotResponseTimeout,
)
from . import Client
# Assuming these are custom imports that need to be adapted for Pyrogram as well
# You'll need to define how `assistant`, `xteam.dB._core`, and `xteam.fns.tools`
# interact with Pyrogram's client and event handling.
from assistant import asst, get_string, inline_pic, udB
from xteam.dB._core import HELP, LIST
from xteam.fns.tools import cmd_regex_replace

# Assuming these are custom imports and variables, define them as needed
# For example, HNDLR would likely be a prefix for commands.
HNDLR = "."  # Example handler prefix
LOGS = print  # Simple print for logging, replace with a proper logger if available
OWNER_NAME = "YourOwnerName"  # Replace with actual owner name

_main_help_menu = [
    [
        InlineKeyboardButton("🏡 Modules 🏡", callback_data="uh_Official_"),
    ],
]

@Client.on_message(filters.command("ahelp", prefixes=HNDLR))
async def _help(client: Client, message):
    plug = message.command[1] if len(message.command) > 1 else None
    chat_id = message.chat.id

    if plug:
        try:
            if plug in HELP["Official"]:
                output = f"**Plugin** - `{plug}`\n"
                for i in HELP["Official"][plug]:
                    output += i
                output += "\n@xteam_cloner"
                await message.reply(f"<blockquote>{output}</blockquote>", parse_mode="html")
            elif HELP.get("Addons") and plug in HELP["Addons"]:
                output = f"**Plugin** - `{plug}`\n"
                for i in HELP["Addons"][plug]:
                    output += i
                output += "\n@xteam_cloner"
                await message.reply(output)
            elif HELP.get("VCBot") and plug in HELP["VCBot"]:
                output = f"**Plugin** - `{plug}`\n"
                for i in HELP["VCBot"][plug]:
                    output += i
                output += "\n@xteam_cloner"
                await message.reply(f"<blockquote>{output}</blockquote>", parse_mode="html")
            else:
                try:
                    x = get_string("help_11").format(plug)
                    for d in LIST[plug]:
                        x += "" + d
                        x += "\n"
                    x += "\n@xteam_cloner"
                    await message.reply(f"<blockquote>{x}</blockquote>", parse_mode="html")
                except KeyError:
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
                        if file:
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
                        return await message.reply(text)

                    output = f"Command {plug} found in plugin - {file}\n"
                    if file in HELP["Official"]:
                        for i in HELP["Official"][file]:
                            output += i
                    elif HELP.get("Addons") and file in HELP["Addons"]:
                        for i in HELP["Addons"][file]:
                            output += i
                    elif HELP.get("VCBot") and file in HELP["VCBot"]:
                        for i in HELP["VCBot"][file]:
                            output += i
                    output += "\n@xteam_cloner"
                    await message.reply(f"<blockquote>{output}</blockquote>", parse_mode="html")
        except Exception as er:
            LOGS(f"Error: {er}")
            await message.reply("Error 🤔 occurred.")
    else:
        try:
            # Pyrogram's `get_inline_bot_results` for inline queries
            results = await client.get_inline_bot_results(asst.me.username, "help")
            await message.reply_inline_bot_result(results.query_id, results.results[0].id)
            await message.delete()
        except BotMethodInvalid:
            z = []
            for x in LIST.values():
                z.extend(x)
            cmd = len(z) + 10
            keyboard = InlineKeyboardMarkup(_main_help_menu)
            if udB.get_key("MANAGER") and udB.get_key("DUAL_HNDLR") == "/":
                # Pyrogram uses InlineKeyboardButton
                _main_help_menu.insert(2, [InlineKeyboardButton("• Manager Help •", callback_data="mngbtn")])
                keyboard = InlineKeyboardMarkup(_main_help_menu) # Recreate keyboard if menu changes
            
            await message.reply_photo(
                photo=inline_pic(), # Assuming inline_pic() returns a file path or bytes
                caption=get_string("inline_4").format(
                    OWNER_NAME,
                    len(HELP["Official"]),
                    len(HELP["Addons"] if "Addons" in HELP else []),
                    cmd,
                ),
                reply_markup=keyboard,
            )
        except BotResponseTimeout:
            await message.reply(get_string("help_2").format(HNDLR))
        except BotInlineDisabled:
            await message.reply(get_string("help_3"))


# --- Callbacks ---
@Client.on_callback_query(filters.regex(r"uh_Official_"))
async def official_help_callback(client, callback_query):
    # This is a placeholder. You'll need to implement the logic
    # for displaying official modules based on your HELP dictionary.
    await callback_query.answer("Displaying official modules...", show_alert=True)
    # Example:
    # modules_text = "Here are the official modules:\n"
    # for module_name in HELP["Official"].keys():
    #     modules_text += f"- {module_name}\n"
    # await callback_query.edit_message_text(modules_text, reply_markup=some_back_button)

# Add other callback handlers similarly, e.g., for "mngbtn"
# @Client.on_callback_query(filters.regex(r"mngbtn"))
# async def manager_help_callback(client, callback_query):
#     await callback_query.answer("Displaying manager help...", show_alert=True)
#     # Implement manager help display

