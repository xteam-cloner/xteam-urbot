import asyncio
from datetime import datetime, timedelta
from telethon import events
from telegraph import upload_file as uf
import time
import pytz
from xteam._misc._decorators import ultroid_cmd
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
)

# Fungsi utilitas untuk mendapatkan waktu mulai dan zona waktu
def get_current_time_and_timezone():
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz)
    # 👇 Format sekarang harus menyertakan tahun (%Y)
    start_time_str = now.strftime("%B %d, %Y, %I:%M %p")
    return start_time_str, now, now.tzname()

def format_afk_duration(start_time_dt):
    # Mengambil waktu saat ini di zona waktu yang sama dengan waktu mulai
    now_dt = datetime.now(start_time_dt.tzinfo)
    delta = now_dt - start_time_dt

    total_seconds = int(delta.total_seconds())

    # Mencegah hasil negatif/error
    if total_seconds < 0:
        total_seconds = 0

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours} Hours, {minutes} Minutes, {seconds} Seconds"

# Pengganti untuk get_string (Tetap sama)
def get_string(key):
    strings = {
        "afk_status": (
            "Since   : <b>{start_time_str}</b>\n"
            "Timezone: <b>{timezone}</b>\n"
            "Reason  : <b>{text}</b>"
        ),
        "afk_back_msg": (
            "I'm back! I was AFK for:\n"
            "<blockquote>{afk_duration}</blockquote>"
        ),
    }
    return strings.get(key, "String not found")

# --- KODE INTI ---

old_afk_msg = []
is_approved = KeyManager("PMPERMIT", cast=list).contains

@ultroid_cmd(pattern="afk( (.*)|$)", owner_only=True)
async def set_afk(event):
    if event.client._bot or is_afk():
        return

    text, media, media_type = None, None, None
    msg1, msg2 = None, None

    if event.pattern_match.group(1).strip():
        text = event.text.split(maxsplit=1)[1]
    else:
        text = "No reason specified"

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

    add_afk(text, media_type, media, start_time_str, timezone)

    ultroid_bot.add_handler(remove_afk, events.NewMessage(outgoing=True))
    ultroid_bot.add_handler(
        on_afk,
        events.NewMessage(
            incoming=True, func=lambda e: bool(e.mentioned or e.is_private)
        ),
    )

    afk_status_msg = get_string("afk_status").format(
        start_time_str=start_time_str,
        timezone=timezone,
        text=text
    )

    # Mengirim status AFK pertama DENGAN parse_mode='html'
    if media:
        if "sticker" in media_type:
            msg1 = await ultroid_bot.send_file(event.chat_id, file=media)
            msg2 = await ultroid_bot.send_message(event.chat_id, f"<blockquote>Away from Keyboard</blockquote>\n\n{afk_status_msg}", parse_mode="html")
        else:
            msg1 = await ultroid_bot.send_message(
                event.chat_id, f"<blockquote>Away from Keyboard</blockquote>\n\n{afk_status_msg}", file=media, parse_mode="html"
            )
    else:
        msg1 = await event.respond(f"<blockquote>Away from Keyboard</blockquote>\n\n{afk_status_msg}", parse_mode="html")

    old_afk_msg.append(msg1)

---

async def remove_afk(event):
    if event.is_private and udB.get_key("PMSETTING") and not is_approved(event.chat_id):
        return
    elif "afk" in event.text.lower():
        return
    elif event.chat_id in NOSPAM_CHAT:
        return

    afk_data = is_afk()
    if afk_data:
        try:
            text, media_type, media, start_time_str, timezone = afk_data
        except ValueError:
            text, media_type, media, _ = afk_data
            start_time_str, timezone = "Unknown", "Unknown"

        # PERBAIKAN KONVERSI WAKTU
        try:
            tz = pytz.timezone('Asia/Jakarta')

            # Format baru harus mencakup tahun (%Y)
            naive_dt = datetime.strptime(start_time_str, "%B %d, %Y, %I:%M %p")
            start_time_dt = tz.localize(naive_dt)
        except Exception:
            # Fallback jika gagal
            tz = pytz.timezone('Asia/Jakarta')
            start_time_dt = datetime.now(tz) - timedelta(seconds=1)

        afk_duration = format_afk_duration(start_time_dt)
        del_afk()

        off = await event.reply(get_string("afk_back_msg").format(afk_duration=afk_duration), parse_mode='html')

        for x in old_afk_msg:
            try:
                await x.delete()
            except BaseException:
                pass
        await asyncio.sleep(10)
        await off.delete()
        

@ultroid_cmd(pattern="unafk$")
async def unafk(event):
    afk_data = is_afk()
    if not afk_data:
        return await event.eor("`You are currently not AFK.`", time=3)
    try:
        text, media_type, media, start_time_str, timezone = afk_data
    except ValueError:
        text, media_type, media, _ = afk_data
        start_time_str, timezone = "Unknown", "Unknown"

    # PERBAIKAN KONVERSI WAKTU
    try:
        tz = pytz.timezone('Asia/Jakarta')

        # Format harus mencakup tahun (%Y)
        naive_dt = datetime.strptime(start_time_str, "%B %d, %Y, %I:%M %p")
        start_time_dt = tz.localize(naive_dt)
    except Exception:
        # Fallback
        tz = pytz.timezone('Asia/Jakarta')
        start_time_dt = datetime.now(tz) - timedelta(seconds=1)

    afk_duration = format_afk_duration(start_time_dt)

    # Hapus status AFK dari database
    del_afk()

    # Kirim pesan kembali/konfirmasi
    off = await event.reply(get_string("afk_back_msg").format(afk_duration=afk_duration), parse_mode='html')

    # Hapus pesan status AFK lama
    for x in old_afk_msg:
        try:
            await x.delete()
        except BaseException:
            pass

    # Hapus pesan konfirmasi setelah 10 detik
    await asyncio.sleep(10)
    await off.delete()

---

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

    try:
        text, media_type, media, start_time_str, timezone = afk_data
    except ValueError:
        text, media_type, media, _ = afk_data
        start_time_str, timezone = "Unknown", "Unknown"

    # PERBAIKAN KONVERSI WAKTU DI SINI
    try:
        tz = pytz.timezone('Asia/Jakarta')

        # Format baru harus mencakup tahun (%Y)
        naive_dt = datetime.strptime(start_time_str, "%B %d, %Y, %I:%M %p")
        start_time_dt = tz.localize(naive_dt)
    except Exception:
        # Fallback
        tz = pytz.timezone('Asia/Jakarta')
        start_time_dt = datetime.now(tz) - timedelta(seconds=1)

    afk_duration = format_afk_duration(start_time_dt)

    status_msg = get_string("afk_status").format(
        start_time_str=start_time_str,
        timezone=timezone,
        text=text if text else "None"
    )

    # Format akhir dengan HTML <code>
    final_text = (
        f"<b>Away from Keyboard</b>\n\n"
        f"{status_msg}\n\n"
        f"<code>{afk_duration}</code>"
    )

    # Mengirim pesan DENGAN parse_mode='html'
    msg1, msg2 = None, None
    if media:
        if "sticker" in media_type:
            msg1 = await event.reply(file=media)
            msg2 = await event.reply(final_text, parse_mode='html')
        else:
            msg1 = await event.reply(final_text, file=media, parse_mode='html')
    else:
        msg1 = await event.reply(final_text, parse_mode='html')

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
        
