from . import get_help

doc = get_help("help_afk")


import asyncio

from telegraph import upload_file as uf
from telethon import events

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

from telethon import Button, events

@ultroid_cmd(pattern="pafk( (.*)|$)", owner_only=True)
async def set_afk(event):
    if event.client._bot or is_afk():
        return
    text, media, media_type = None, None, None
    if event.pattern_match.group(1).strip():
        text = event.text.split(maxsplit=1)[1]
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
    await event.eor("Done", time=2)
    add_afk(text, media_type, media)
    asst.add_handler(remove_afk, events.NewMessage(outgoing=True))
    asst.add_handler(
        on_afk,
        events.NewMessage(
            incoming=True, func=lambda e: bool(e.mentioned or e.is_private)
        ),
    )
    
    msg1, msg2 = None, None
    
    # Membuat tombol "Selesai" dengan callback data
    selesai_button = Button.inline('✅ Selesai', data=b'disable_afk')

    if text and media:
        if "sticker" in media_type:
            msg1 = await asst.send_file(event.chat_id, file=media, buttons=[[selesai_button]])
            msg2 = await asst.send_message(
                event.chat_id, get_string("afk_5").format(text)
            )
        else:
            msg1 = await asst.send_message(
                event.chat_id, get_string("afk_5").format(text), file=media, buttons=[[selesai_button]]
            )
    elif media:
        if "sticker" in media_type:
            msg1 = await asst.send_file(event.chat_id, file=media, buttons=[[selesai_button]])
            msg2 = await asst.send_message(event.chat_id, get_string("afk_6"))
        else:
            msg1 = await asst.send_message(
                event.chat_id, get_string("afk_6"), file=media, buttons=[[selesai_button]]
            )
    elif text:
        msg1 = await event.respond(get_string("afk_5").format(text), buttons=[[selesai_button]])
    else:
        msg1 = await event.respond(get_string("afk_6"), buttons=[[selesai_button]])
        
    old_afk_msg.append(msg1)
    if msg2:
        old_afk_msg.append(msg2)
        return await asst.send_message(LOG_CHANNEL, msg2.text)
    await asst.send_message(LOG_CHANNEL, msg1.text)

# Handler untuk tombol "Selesai"
@asst.on(events.CallbackQuery(data=b'disable_afk'))
async def disable_afk_handler(event):
    if is_afk():
        await remove_afk(event)
        await event.edit("Mode AFK telah dinonaktifkan.")
    else:
        await event.edit("Anda tidak dalam mode AFK.")
