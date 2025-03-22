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

from . import HNDLR, LOGS, OWNER_NAME, asst, get_string, udB, ultroid_cmd

_main_help_menu = [
    [Button.inline("ᴍᴏᴅᴜʟᴇꜱ", data="uh_Official_")],
    [Button.inline("ᴄʟᴏꜱᴇ", data="close")],
]


@ultroid_cmd(pattern="helper( (.*)|$)")
async def _help(ult):
    plug = ult.pattern_match.group(1).strip()
    chat = await ult.get_chat()
    
    if plug:  # If specific plugin is provided
        try:
            if plug in HELP.get("Official", {}):
                output = f"**Plugin** - `{plug}`\n" + "\n".join(HELP["Official"][plug])
            elif HELP.get("Addons") and plug in HELP["Addons"]:
                output = f"**Plugin** - `{plug}`\n" + "\n".join(HELP["Addons"][plug])
            elif HELP.get("VCBot") and plug in HELP["VCBot"]:
                output = f"**Plugin** - `{plug}`\n" + "\n".join(HELP["VCBot"][plug])
            else:  # If plugin is not found
                file, best_match = None, None
                compare_strings = [cmd_regex_replace(cmd) for cmd_list in LIST.values() for cmd in cmd_list]
                for cmd in compare_strings:
                    if cmd.strip() == plug:
                        file = next(f for f in LIST if plug in LIST[f])
                        break
                    if plug in cmd and not cmd.startswith("_"):
                        best_match = cmd

                if file:
                    output = f"**Command** `{plug}` **found in plugin** - `{file}`\n" + "\n".join(HELP.get(file, []))
                else:
                    text = f"`{plug}` is not a valid plugin!"
                    if best_match:
                        text += f"\nDid you mean `{best_match}`?"
                    return await ult.eor(text)

            output += "\n© @xteam_cloner"
            await ult.eor(output)
        except Exception as er:
            LOGS.exception(er)
            await ult.eor("Error 🤔 occurred.")
    else:  # Show modules button if no specific plugin is mentioned
        try:
            results = await ult.client.inline_query(asst.me.username, "ultd")
            await results[0].click(chat.id, reply_to=ult.reply_to_msg_id, hide_via=True)
            await ult.delete()
        except BotMethodInvalidError:
            return await ult.reply(
                get_string("inline_4").format(
                    OWNER_NAME,
                    len(HELP.get("Official", [])),
                    len(HELP.get("Addons", [])),
                    sum(len(v) for v in LIST.values()) + 10,
                ),
                buttons=_main_help_menu,
            )
        except BotResponseTimeoutError:
            await ult.eor(get_string("help_2").format(HNDLR))
        except BotInlineDisabledError:
            await ult.eor(get_string("help_3"))
                      
