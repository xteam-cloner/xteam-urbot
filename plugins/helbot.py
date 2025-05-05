from telethon.errors.rpcerrorlist import (
    BotInlineDisabledError,
    BotMethodInvalidError,
    BotResponseTimeoutError,
)
from telethon.tl.custom import Button
from telethon.tl.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import re

from pyUltroid.dB._core import HELP, LIST
from pyUltroid.fns.tools import cmd_regex_replace

from . import HNDLR, LOGS, OWNER_NAME, asst, get_string, inline_pic, udB, ultroid_cmd
from pyrogram import Client, Message

async def get_arg(message):
    if message.text:
        return message.text.split()[1:]
    return None


async def get_prefix(user_id):
    # Replace this with your actual logic to get prefixes for a user
    # This is just a placeholder
    return [".", "!"]


def paginate_modules(page_number, module_dict, prefix):
    n_per_page = 6
    mod = list(module_dict.keys())
    k = mod[page_number * n_per_page : (page_number + 1) * n_per_page]
    buttons = [
        [
            InlineKeyboardButton(
                text=module.replace("_", " ").title(),
                callback_data=f"help_module({module})",
            )
        ]
        for module in k
    ]
    if len(mod) > n_per_page:
        rows = []
        if page_number > 0:
            rows.append(
                InlineKeyboardButton(
                    text="<", callback_data=f"help_prev({page_number - 1})"
                )
            )
        if page_number < (len(mod) // n_per_page):
            rows.append(
                InlineKeyboardButton(
                    text=">", callback_data=f"help_next({page_number + 1})"
                )
            )
        buttons.append(rows)
    return buttons


# Assuming HELP_COMMANDS is a dictionary containing module names and their help strings
# Example:
HELP_COMMANDS = {
    "start": {
        "__HELP__": "{0}start\n**»** Starts the bot."
    },
    "ping": {
        "__HELP__": "{0}ping\n**»** Checks if the bot is alive."
    },
    "echo": {
        "__HELP__": "{0}echo <text>\n**»** Repeats the given text."
    },
    # Add more modules and their help strings here
}

# Assuming bot is a Telethon client instance
# Example:
# from telethon import TelegramClient
# bot = TelegramClient("bot_session", API_ID, API_HASH)
# await bot.connect()

@ultroid_cmd(pattern="help( (.*)|$)")
async def help_cmd(client, message):
    args = await get_arg(message)
    if not args:
        try:
            if hasattr(client, 'get_inline_bot_results') and hasattr(client, 'me') and client.me and hasattr(client.me, 'username'):
                x = await client.get_inline_bot_results(client.me.username, "help")
                if x and x.results:
                    await message.reply_inline_bot_result(x.query_id, x.results[0].id)
                else:
                    await message.reply("Gagal mendapatkan hasil inline.")
            else:
                await message.reply("Bot tidak memiliki username atau fungsi inline tidak tersedia.")
        except Exception as error:
            await message.reply(f"Terjadi kesalahan: {error}")
    else:
        nama = args[0]
        if nama in HELP_COMMANDS:
            prefixes = await get_prefix(message.sender_id)
            await message.reply(
                HELP_COMMANDS[nama]["__HELP__"].format(
                    next((p) for p in prefixes)
                )
                + f"\n<b>© {client.me.mention if hasattr(client, 'me') and client.me else 'Bot'}</b>",
                quote=True,
            )
        else:
            await message.reply(f"<b>❌ Tidak ada modul bernama <code>{nama}</code></b>")


async def menu_inline(client, inline_query):
    user_id = inline_query.from_user.id
    emut = await get_prefix(user_id)
    msg = "<b>Help Modules\n     Prefixes: `{}`\n     Commands: <code>{}</code></b>".format(
        " ".join(emut), len(HELP_COMMANDS)
    )
    await client.answer_inline_query(
        inline_query.id,
        cache_time=0,
        results=[
            (
                InlineQueryResultArticle(
                    title="Help Menu!",
                    reply_markup=InlineKeyboardMarkup(
                        paginate_modules(0, HELP_COMMANDS, "help")
                    ),
                    input_message_content=InputTextMessageContent(msg),
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
        if module in HELP_COMMANDS:
            text = f"<b>{HELP_COMMANDS[module]['__HELP__']}</b>\n".format(
                next((p) for p in prefix)
            )
            button = [[InlineKeyboardButton("Kembali", callback_data="help_back")]]
            await callback_query.edit_message_text(
                text=text + f"\n<b>© {client.me.mention if hasattr(client, 'me') and client.me else 'Bot'}</b>",
                reply_markup=InlineKeyboardMarkup(button),
                disable_web_page_preview=True,
            )
        else:
            await callback_query.answer("Modul tidak ditemukan.", show_alert=True)
    top_text = "<b>Help Modules\n     Prefixes: <code>{}</code>\n     Commands: <code>{}</code></b>".format(
        " ".join(prefix), len(HELP_COMMANDS)
    )

    if prev_match:
        curr_page = int(prev_match.group(1))
        await callback_query.edit_message_text(
            text=top_text,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(curr_page - 1, HELP_COMMANDS, "help")
            ),
            disable_web_page_preview=True,
        )
    if next_match:
        next_page = int(next_match.group(1))
        await callback_query.edit_message_text(
            text=top_text,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(next_page + 1, HELP_COMMANDS, "help")
            ),
            disable_web_page_preview=True,
        )
    if back_match:
        await callback_query.edit_message_text(
            text=top_text,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(0, HELP_COMMANDS, "help")
            ),
            disable_web_page_preview=True,
        )
              
