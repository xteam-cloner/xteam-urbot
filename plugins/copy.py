import os
import re
import time
import asyncio
from datetime import datetime as dt

from telethon.errors.rpcerrorlist import MessageNotModifiedError

from . import LOGS, time_formatter, downloader, random_string, ultroid_cmd
from . import *

REGEXA = r"^(?:(?:https|tg):\/\/)?(?:www\.)?(?:t\.me\/|openmessage\?)(?:(?:c\/(\d+))|(\w+)|(?:user_id\=(\d+)))(?:\/|&message_id\=)(\d+)(?:\?single)?$"

@ultroid_cmd(
    pattern="cmedia(?: |$)((?:.|\n)*)",
)
async def fwd_dl(e):
    ghomst = await e.eor("`checking...`")
    args = e.pattern_match.group(1)
    if not args:
        reply = await e.get_reply_message()
        if reply and reply.text:
            args = reply.message
        else:
            return await eod(ghomst, "Give a tg link to download", time=10)
    
    remgx = re.findall(REGEXA, args)
    if not remgx:
        return await ghomst.edit("`probably a invalid Link !?`")

    try:
        chat, id = [i for i in remgx[0] if i]
        channel = int(chat) if chat.isdigit() else chat
        msg_id = int(id)
    except Exception as ex:
        return await ghomst.edit("`Give a valid tg link to proceed`")

    try:
        msg = await e.client.get_messages(channel, ids=msg_id)
    except Exception as ex:
        return await ghomst.edit(f"**Error:** `{ex}`")

    start_ = dt.now()
    if msg and msg.media:
        await ghomst.edit("`Uploading to chat...`")
        try:
            # Gunakan event.chat_id untuk mendapatkan ID chat saat ini
            chat_id_tujuan = e.chat_id
            await e.client.send_file(chat_id_tujuan, file=msg.media, caption="File downloaded from a forward-restricted message.")
            
            end_ = dt.now()
            ts = time_formatter(((end_ - start_).seconds) * 1000)
            await ghomst.edit(f"**Successfully uploaded to chat in {ts} !!**")
        except Exception as err:
            LOGS.exception(err)
            return await ghomst.edit(f"**Failed to upload:** `{err}`")

    else:
        return await ghomst.edit("`Message doesn't contain any media to download.`")
      
