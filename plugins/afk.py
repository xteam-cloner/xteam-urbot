# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

from . import get_help

__doc__ = get_help("help_afk")


import asyncio
from datetime import datetime
from telethon import events
from telegraph import upload_file as uf
import time
from xteam.dB.afk_db import add_afk, del_afk, is_afk
from xteam.dB.base import KeyManager
from . import (
    LOG_CHANNEL,
    NOSPAM_CHAT,
    Redis,
    asst,
    get_string,
    mediainfo,
    udB,
    ultroid_bot,
    ultroid_cmd,
)

# Anggap ini adalah fungsi utilitas untuk mendapatkan waktu mulai dan zona waktu
def get_current_time_and_timezone():
    # Mengambil zona waktu UTC+7 (WIB) seperti di gambar
    tz = pytz.timezone('Asia/Jakarta') 
    now = datetime.now(tz)
    
    # Format waktu mulai (misal: "October 26, 7:13 AM")
    start_time_str = now.strftime("%B %d, %I:%M %p")
    
    return start_time_str, now, now.tzname() 

def format_afk_duration(start_time_dt):
    # start_time_dt adalah objek datetime dengan timezone
    delta = datetime.now(pytz.utc).astimezone(start_time_dt.tzinfo) - start_time_dt
    
    total_seconds = int(delta.total_seconds())
    
    # Menghitung jam, menit, detik
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    # Format sesuai gambar: "7 Hours, 33 Minutes, 41 Seconds"
    return f"{hours} Hours, {minutes} Minutes, {seconds} Seconds"

# Pengganti untuk get_string
def get_string(key):
    strings = {
        "afk_status": (
            "Since   : **{start_time_str}**\n"
            "Timezone: **{timezone}**\n"
            "Reason  : **{text}**"
        ),
        "afk_back_msg": "I'm back! I was AFK for:\n**`{afk_duration}`**",
    }
    return strings.get(key, "String not found")

# --- KODE INTI MODIFIKASI ---

old_afk_msg = []
is_approved = KeyManager("PMPERMIT", cast=list).contains

@ultroid_cmd(pattern="afk( (.*)|$)", owner_only=True)
async def set_afk(event):
    if event.client._bot or is_afk():
        return
    
    text, media, media_type = None, None, None
    if event.pattern_match.group(1).strip():
        # Alasan AFK (misal: "turu")
        text = event.text.split(maxsplit=1)[1] 
    else:
        text = "No reason specified" # Alasan default jika tidak ada

    # --- PERUBAHAN UTAMA DI SINI ---
    # Mendapatkan waktu mulai dan zona waktu
    start_time_str, start_time_dt, timezone = get_current_time_and_timezone()
    
    reply = await event.get_reply_message()
    if reply:
        if reply.text and not text:
            text = reply.text
        if reply.media:
            media_type = mediainfo(reply.media)
            if media_type.startswith(("pic", "gif")):
                file = await event.client.download_media(reply.media)
                iurl = uf(file)
                media = f"https://graph.org{iurl[0]}"
            else:
                media = reply.file.id
                
    await event.eor("`Done`", time=2)
    
    # *ASUMSI*: add_afk sekarang menyimpan start_time_str dan timezone
    # Anda harus memodifikasi afk_db.py untuk menerima parameter ini
    add_afk(text, media_type, media, start_time_str, timezone) 
    
    ultroid_bot.add_handler(remove_afk, events.NewMessage(outgoing=True))
    ultroid_bot.add_handler(
        on_afk,
        events.NewMessage(
            incoming=True, func=lambda e: bool(e.mentioned or e.is_private)
        ),
    )
    
    # Membuat pesan status AFK yang akan ditampilkan di log
    afk_status_msg = get_string("afk_status").format(
        start_time_str=start_time_str,
        timezone=timezone,
        text=text
    )
    
    # Mengirim status AFK pertama
    msg1, msg2 = None, None
    
    # Tampilkan status lengkap ke diri sendiri (dan log)
    if media:
        if "sticker" in media_type:
            msg1 = await ultroid_bot.send_file(event.chat_id, file=media)
            msg2 = await ultroid_bot.send_message(event.chat_id, f"**Away from Keyboard**\n\n{afk_status_msg}")
        else:
            msg1 = await ultroid_bot.send_message(
                event.chat_id, f"**Away from Keyboard**\n\n{afk_status_msg}", file=media
            )
    else:
        msg1 = await event.respond(f"**Away from Keyboard**\n\n{afk_status_msg}")
        
    old_afk_msg.append(msg1)
    if msg2:
        old_afk_msg.append(msg2)
        await asst.send_message(LOG_CHANNEL, msg2.text)
    else:
        await asst.send_message(LOG_CHANNEL, msg1.text)


async def remove_afk(event):
    if event.is_private and udB.get_key("PMSETTING") and not is_approved(event.chat_id):
        return
    elif "afk" in event.text.lower():
        return
    elif event.chat_id in NOSPAM_CHAT:
        return
    
    afk_data = is_afk()
    if afk_data:
        # *ASUMSI*: is_afk() mengembalikan (text, media_type, media, start_time_str, timezone)
        try:
            text, media_type, media, start_time_str, timezone = afk_data
        except ValueError:
            # Fallback jika struktur database tidak dimodifikasi
            text, media_type, media, _ = afk_data
            start_time_str, timezone = "Unknown", "Unknown"
        
        # Mengonversi kembali string waktu ke objek datetime untuk perhitungan
        try:
            tz = pytz.timezone(timezone) # Gunakan timezone yang tersimpan
            start_time_dt = datetime.strptime(start_time_str, "%B %d, %I:%M %p").replace(tzinfo=tz)
        except:
            # Jika gagal, gunakan waktu saat ini sebagai waktu mulai (kurang akurat)
            start_time_dt = datetime.fromtimestamp(time.time(), pytz.UTC) 
            
        afk_duration = format_afk_duration(start_time_dt)
        
        del_afk()
        
        # Mengirim pesan kembali dengan durasi AFK dalam format bubble
        off = await event.reply(get_string("afk_back_msg").format(afk_duration=afk_duration))
        await asst.send_message(LOG_CHANNEL, f"AFK ended. Duration: {afk_duration}")
        
        for x in old_afk_msg:
            try:
                await x.delete()
            except BaseException:
                pass
        await asyncio.sleep(10)
        await off.delete()


async def on_afk(event):
    if event.is_private and Redis("PMSETTING") and not is_approved(event.chat_id):
        return
    elif "afk" in event.text.lower():
        return
    elif not is_afk():
        return
    if event.chat_id in NOSPAM_CHAT:
        return
    sender = await event.get_sender()
    if sender.bot or sender.verified:
        return
        
    afk_data = is_afk()
    if not afk_data: return
    
    # *ASUMSI*: is_afk() mengembalikan (text, media_type, media, start_time_str, timezone)
    try:
        text, media_type, media, start_time_str, timezone = afk_data
    except ValueError:
        text, media_type, media, _ = afk_data
        start_time_str, timezone = "Unknown", "Unknown"

    # Mengonversi kembali string waktu ke objek datetime untuk perhitungan
    try:
        tz = pytz.timezone(timezone) # Gunakan timezone yang tersimpan
        start_time_dt = datetime.strptime(start_time_str, "%B %d, %I:%M %p").replace(tzinfo=tz)
    except:
        start_time_dt = datetime.fromtimestamp(time.time(), pytz.UTC) # Fallback

    # 1. Menghitung durasi AFK saat ini
    afk_duration = format_afk_duration(start_time_dt)

    # 2. Membuat pesan status AFK (Since, Timezone, Reason)
    status_msg = get_string("afk_status").format(
        start_time_str=start_time_str,
        timezone=timezone,
        text=text if text else "None"
    )

    final_text = (
        f"**Away from Keyboard**\n\n"
        f"{status_msg}\n\n"
        f"`{afk_duration}`"
    )

    msg1, msg2 = None, None
    if media:
        if "sticker" in media_type:
            msg1 = await event.reply(file=media)
            msg2 = await event.reply(final_text)
        else:
            msg1 = await event.reply(final_text, file=media)
    else:
        msg1 = await event.reply(final_text)
        
    for x in old_afk_msg:
        try:
            await x.delete()
        except BaseException:
            pass
            
    old_afk_msg.append(msg1)
    if msg2:
        old_afk_msg.append(msg2)


if udB.get_key("AFK_DB"):
    ultroid_bot.add_handler(remove_afk, events.NewMessage(outgoing=True))
    ultroid_bot.add_handler(
        on_afk,
        events.NewMessage(
            incoming=True, func=lambda e: bool(e.mentioned or e.is_private)
        ),
    )
