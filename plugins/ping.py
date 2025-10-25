# UserBot
# Copyright (C) 2021-2023 Teamx-cloner
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

from . import get_help

__doc__ = get_help("help_bot")

import asyncio
import os
import sys
import time
import random
from telethon.errors import FloodWaitError
from telethon import Button
from telethon import events, TelegramClient
from telethon.tl.functions import PingRequest
from secrets import choice
from telethon.tl.types import (
    InputMessagesFilterVideo,
    InputMessagesFilterVoice,
    InputMessagesFilterPhotos,
)
from xteam._misc import sudoers
from xteam.fns.custom_markdown import CustomMarkdown
from xteam.fns.helper import download_file, inline_mention
from ._inline import *
from xteam.fns.helper import inline_mention
from . import (
    OWNER_NAME,
    OWNER_ID,
    BOT_NAME,
    OWNER_USERNAME,
    asst,
    start_time,
    time_formatter,
    udB,
    ultroid_cmd as xteam_cmd,
    get_string,
    ultroid_bot,
    eor,
    ultroid_bot,
    call_back,
    callback,
)


async def mention_user(user_id):
    try:
        user_entity = await ultroid_bot.get_entity(user_id)
        first_name = user_entity.first_name
        mention_text = f"[{first_name}](tg://user?id={user_id})"
        return mention_text
    except Exception as e:
        print(f"Failed to mention user: {e}")


@xteam_cmd(pattern="ping(|x|s)$", chats=[], type=["official", "assistant"])
async def _(event):
    ultroid_bot.parse_mode = CustomMarkdown()
    user_id = OWNER_ID
    ment = await mention_user(user_id)
    bot_header = f"```𖤓⋆Mʏꜱᴛᴇʀɪᴏᴜꜱ Gɪʀʟꜱ⋆𖤓```"
    prem = event.pattern_match.group(1)
    start = time.time()
    x = await event.reply("ping")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    if prem == "x":
        await x.reply(get_string("pping").format(end, uptime))
    elif prem == "s":
        await x.reply(get_string("iping").format(end))
    else:
        pic = udB.get_key("PING_PIC")
        await asyncio.sleep(0,5)
        await x.edit(get_string("ping").format(bot_header, end, uptime, f"{OWNER_NAME}"), file=pic)
    

@xteam_cmd(pattern="Ping$", chats=[], type=["official", "assistant"])
async def _(event):
    ultroid_bot.parse_mode = CustomMarkdown()
    user_id = OWNER_ID
    ment = await mention_user(user_id)
    start = time.time()
    x = await event.reply("Ping")
    end = round((time.time() - start) * 1000)  # Corrected to milliseconds
    uptime = time_formatter((time.time() - start_time) * 1000)  # Corrected to milliseconds
    await x.reply(get_string("pping").format(end, uptime, OWNER_NAME))
    #await x.edit(f"🏓 Pong • {end}ms\n⏰ Uptime • {uptime}\n👑 Owner • {OWNER_NAME}")

# ... (Semua impor dan kode di atas tetap sama)

# ... (Fungsi mention_user tetap sama)

@xteam_cmd(pattern="xping(|x|s)$", chats=[], type=["official", "assistant"])
async def _(event):
    ultroid_bot.parse_mode = CustomMarkdown()
    
    # 1. Mendapatkan ID Pengguna yang Menjalankan Perintah
    user_id = event.sender_id
    
    # Menyiapkan variabel umum
    prem = event.pattern_match.group(1)
    start = time.time()
    
    # Memberikan respons "ping" awal untuk mengukur latency
    x = await event.reply("ping")
    
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    
    # Menentukan status pengguna untuk output yang berbeda
    is_owner = user_id == OWNER_ID
    is_sudo = user_id in sudoers
    
    # --- Pilihan ping yang berbeda (pingx/pings) ---
    if prem == "x":
        # Output singkat untuk 'pingx'
        await x.reply(get_string("pping").format(end, uptime))
        return # Keluar dari fungsi setelah mengirim
        
    elif prem == "s":
        # Output latensi saja untuk 'pings'
        await x.reply(get_string("iping").format(end))
        return # Keluar dari fungsi setelah mengirim

    # --- Output utama (ping) ---
    
    # Variabel yang akan digunakan dalam pesan akhir
    user_role = ""
    pic = udB.get_key("PING_PIC")
    bot_header = f"```𖤓⋆Mʏꜱᴛᴇʀɪᴏᴜꜱ Gɪʀʟꜱ⋆𖤓```"
    
    if is_owner:
        # PING untuk OWNER
        user_role = "**[👑 OWNER]**"
        # Kita juga bisa mendapatkan mention untuk OWNER_ID
        ment = await mention_user(OWNER_ID)
        ping_message = get_string("ping").format(
            bot_header, 
            end, 
            uptime, 
            f"{ment} {user_role}" # Menambahkan peran dan mention Owner
        )
        
    elif is_sudo:
        # PING untuk SUDO_USERS
        user_role = "**[⚙️ SUDO USER]**"
        ping_message = get_string("ping").format(
            bot_header, 
            end, 
            uptime, 
            f"{OWNER_NAME} {user_role}" # Misalnya, hanya menampilkan nama Owner tapi menyebut peran eksekutor
        )
        # Anda mungkin ingin mendapatkan mention untuk sudo user, bukan owner:
        # sudo_ment = await mention_user(user_id)
        # ping_message = get_string("ping").format(bot_header, end, uptime, f"{sudo_ment} {user_role}")
        
    else:
        # PING untuk PENGGUNA BIASA (Non-Owner/Non-Sudo)
        user_role = "" # Tidak perlu peran
        ping_message = get_string("ping").format(
            bot_header, 
            end, 
            uptime, 
            f"{OWNER_NAME}" # Hanya menampilkan nama Owner
        )
        
    await asyncio.sleep(0.5)
    await x.edit(ping_message, file=pic)
