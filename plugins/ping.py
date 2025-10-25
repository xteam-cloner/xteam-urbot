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

@xteam_cmd(pattern="ping(|x|s)$", chats=[], type=["official", "assistant"])
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
    # Dapatkan client dari event untuk mengambil detail user
    client = event.client 
    
    # --- 1. Ganti Parse Mode menjadi HTML ---
    # Setting ini diabaikan oleh x.edit(parse_mode='html'), tapi biarkan jika framework butuh
    ultroid_bot.parse_mode = "html" 
    
    user_id = event.sender_id
    prem = event.pattern_match.group(1)
    start = time.time()
    x = await event.reply("ping")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    
    # --- Penentuan Status Pengguna ---
    is_owner = user_id == OWNER_ID
    is_full_sudo = user_id in SUDO_M.fullsudos 
    is_standard_sudo = user_id in sudoers()
    
    # --- Output Singkat (pingx/pings) ---
    if prem == "x":
        await x.reply(get_string("pping").format(end, uptime))
        return
        
    elif prem == "s":
        await x.reply(get_string("iping").format(end))
        return

    # --- Output utama (ping) ---
    
    # --- Dapatkan Objek Owner untuk Link HTML ---
    owner_entity = await client.get_entity(OWNER_ID)
    owner_name = owner_entity.first_name or owner_entity.title # Ambil nama owner
    
    # --- 2. Ambil ID Custom Emoji dari DB dan Tentukan Format ---
    pic = udB.get_key("PING_PIC")
    
    EMOJI_PING_ID = udB.get_key("EMOJI_PING") 
    EMOJI_UPTIME_ID = udB.get_key("EMOJI_UPTIME")
    EMOJI_OWNER_ID = udB.get_key("EMOJI_OWNER")
    
    # Logika Custom Emoji (Sama seperti sebelumnya, sudah benar)
    if EMOJI_PING_ID:
        EMOJI_PING_HTML = f'<a href="emoji/{EMOJI_PING_ID}">✔️</a>' 
    else:
        EMOJI_PING_HTML = '✔️'
        
    if EMOJI_UPTIME_ID:
        EMOJI_UPTIME_HTML = f'<a href="emoji/{EMOJI_UPTIME_ID}">⏰</a>'
    else:
        EMOJI_UPTIME_HTML = '⏰'
        
    if EMOJI_OWNER_ID:
        EMOJI_OWNER_HTML = f'<a href="emoji/{EMOJI_OWNER_ID}">👑</a>'
    else:
        EMOJI_OWNER_HTML = '👑'
    
    bot_header_text = "𖤓⋆Mʏꜱᴛᴇʀɪᴏᴜꜱ Gɪʀʟꜱ⋆𖤓" 
    
    # Pengecekan peran dengan prioritas tertinggi ke terendah
    # --- KOREKSI: Gunakan Link HTML Murni untuk Mentions ---
    if is_owner:
        user_role = "<b>OWNER</b>"
        # 🟢 Buat link HTML murni untuk owner
        owner_html_mention = f"<a href='tg://user?id={OWNER_ID}'>{owner_name}</a>"
        display_name = f"{user_role} : {owner_html_mention}" 
        
    elif is_full_sudo:
        user_role = "<b>FULLSUDO</b>" 
        # 🟢 Asumsikan 'mention_user' menghasilkan nama pengguna untuk link (atau perlu diubah juga)
        sudo_ment = await client.get_entity(user_id) # Ambil entity untuk nama
        sudo_name = sudo_ment.first_name or sudo_ment.title
        sudo_html_mention = f"<a href='tg://user?id={user_id}'>{sudo_name}</a>"
        display_name = f"{user_role} : {sudo_html_mention}"
        
    elif is_standard_sudo:
        user_role = "<b>SUDOUSER</b>" 
        # 🟢 Sama, buat link HTML untuk Standard Sudo
        sudo_ment = await client.get_entity(user_id)
        sudo_name = sudo_ment.first_name or sudo_ment.title
        sudo_html_mention = f"<a href='tg://user?id={user_id}'>{sudo_name}</a>"
        display_name = f"{user_role} : {sudo_html_mention}"
        
    else:
        # Pengguna Biasa
        user_role = ""
        # 🟢 Buat link HTML untuk Owner (tetap menampilkan link owner)
        owner_html_mention = f"<a href='tg://user?id={OWNER_ID}'>{owner_name}</a>"
        display_name = f"{owner_html_mention}" # Hanya tampilkan link owner
        
    # --- 3. Format pesan akhir: Blockquote HTML (<blockquote>) ---
    ping_message = f"""
<blockquote>
<b>{bot_header_text}</b>
{EMOJI_PING_HTML} Ping : {end}ms
{EMOJI_UPTIME_HTML} Uptime : {uptime}
{EMOJI_OWNER_HTML} {display_name}
</blockquote>
"""
        
    await asyncio.sleep(0.5)
    
    # Edit pesan dengan parse_mode='html' (Sudah benar)
    await x.edit(ping_message, file=pic, parse_mode='html')
    
