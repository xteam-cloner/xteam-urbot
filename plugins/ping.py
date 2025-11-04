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
from xteam._misc import SUDO_M, sudoers 
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

@xteam_cmd(pattern="xping(|x|s)$", chats=[], type=["official", "assistant"])
async def _(event):
    ultroid_bot.parse_mode = CustomMarkdown()
    user_id = event.sender_id
    prem = event.pattern_match.group(1)
    start = time.time()
    x = await event.reply("ping")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    
    # --- Penentuan Status Pengguna ---
    is_owner = user_id == OWNER_ID
    # Gunakan SUDO_M.fullsudos untuk full sudo access (owner sudah termasuk di dalamnya)
    is_full_sudo = user_id in SUDO_M.fullsudos 
    # Gunakan sudoers() untuk standard sudo access
    is_standard_sudo = user_id in sudoers()
    
    # --- Output Singkat (pingx/pings) ---
    if prem == "x":
        await x.reply(get_string("pping").format(end, uptime))
        return
        
    elif prem == "s":
        await x.reply(get_string("iping").format(end))
        return

    # --- Output utama (ping) ---
    
    pic = udB.get_key("PING_PIC")
    bot_header = f"```𖤓⋆Mʏꜱᴛᴇʀɪᴏᴜꜱ Gɪʀʟꜱ⋆𖤓```"
    
    # Pengecekan peran dengan prioritas tertinggi ke terendah
    if is_owner:
        user_role = "**OWNER**"
        ment = await mention_user(OWNER_ID)
        display_name = f"{user_role} : {ment}"
        
    elif is_full_sudo:
        # Full Sudo (Tidak termasuk Owner, karena sudah dicek di atas)
        user_role = "**FULLSUDO**"
        sudo_ment = await mention_user(user_id)
        display_name = f"{user_role} : {sudo_ment}"
        
    elif is_standard_sudo:
        # Standard Sudo
        user_role = "**SUDOUSER**"
        sudo_ment = await mention_user(user_id)
        display_name = f"{user_role} : {sudo_ment}"
        
    else:
        # Pengguna Biasa
        user_role = ""
        display_name = f"{OWNER_NAME}" # Default: tampilkan nama Owner
        
    # Format pesan akhir
    ping_message = get_string("ping").format(
        bot_header, 
        end, 
        uptime, 
        display_name
    )
        
    await asyncio.sleep(0.5)
    await x.edit(ping_message, file=pic)

        
@xteam_cmd(pattern="ping(|x|s)$", chats=[], type=["official", "assistant"])
async def _(event):
    client = event.client 
    ultroid_bot.parse_mode = "html" 
    
    user_id = event.sender_id
    prem = event.pattern_match.group(1)
    start = time.time()
    x = await event.reply("ping")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    
    is_owner = user_id == OWNER_ID
    is_full_sudo = user_id in SUDO_M.fullsudos 
    is_standard_sudo = user_id in sudoers()
    
    if prem == "x":
        await x.reply(get_string("pping").format(end, uptime))
        return
        
    elif prem == "s":
        await x.reply(get_string("iping").format(end))
        return

    owner_entity = await client.get_entity(OWNER_ID)
    owner_name = owner_entity.first_name 
    
    pic = udB.get_key("PING_PIC")
    
    # --- PERBAIKAN: Selalu konversi nilai dari DB ke string (str()) ---
    
    # Ambil nilai. Jika ditemukan (bukan None/False), konversi ke str, jika tidak, gunakan default "🏓".
    emoji_ping_base = udB.get_key("EMOJI_PING") 
    emoji_ping_html = (str(emoji_ping_base) if emoji_ping_base else "🏓") + " "
    
    # Ambil nilai. Jika ditemukan, konversi ke str, jika tidak, gunakan default "⏰".
    emoji_uptime_base = udB.get_key("EMOJI_UPTIME")
    emoji_uptime_html = (str(emoji_uptime_base) if emoji_uptime_base else "⏰") + " "
    
    # Ambil nilai. Jika ditemukan, konversi ke str, jika tidak, gunakan default "👑".
    # Ini memperbaiki baris yang menyebabkan error 'int' dan 'str'.
    emoji_owner_base = udB.get_key("EMOJI_OWNER")
    emoji_owner_html = (str(emoji_owner_base) if emoji_owner_base else "👑") + " "
    
    # ------------------------------------------------------------------
    
    bot_header_text = "𖤓⋆<a href='https://github.com/xteam-cloner/xteam-urbot'>xᴛᴇᴀᴍ ᴜʀʙᴏᴛ</a>⋆𖤓" 
    
    if is_full_sudo or is_standard_sudo:
        current_user_entity = await client.get_entity(user_id)
        current_user_name = current_user_entity.first_name or current_user_entity.title
        user_html_mention = f"<a href='tg://user?id={user_id}'>{current_user_name}</a>"
    else:
        user_html_mention = f"{owner_name}" 

    owner_html_mention = f"<a href='tg://user?id={OWNER_ID}'>{owner_name}</a>"
    
    if is_owner:
        user_role = "OWNER"
        display_name = f"{user_role} : {owner_html_mention}" 
        
    elif is_full_sudo:
        user_role = "FULLSUDO" 
        display_name = f"{user_role} : {user_html_mention}"
        
    elif is_standard_sudo:
        user_role = "SUDOUSER" 
        display_name = f"{user_role} : {user_html_mention}"
        
    else:
        user_role = ""
        display_name = f"{owner_html_mention}" 
        
    ping_message = f"""
<blockquote>
<b>{bot_header_text}</b></blockquote>
<blockquote>{emoji_ping_html} Ping : {end}ms
{emoji_uptime_html} Uptime : {uptime}
{emoji_owner_html} {display_name}
</blockquote>
"""
        
    await asyncio.sleep(0.5)
    await x.edit(ping_message, file=pic, parse_mode='html')
        
