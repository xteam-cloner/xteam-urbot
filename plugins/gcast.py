# xteam - UserBot
# Copyright (C) 2021-2022 senpai80
#
# This file is a part of < https://github.com/senpai80/xteam/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/senpai80/xteam/blob/main/LICENSE/>.
"""
✘ **Bantuan Untuk Broadcast**

๏ **Perintah:** `gcast`
◉ **Keterangan:** Kirim pesan ke semua obrolan grup.

๏ **Perintah:** `gucast`
◉ **Keterangan:** Kirim pesan ke semua pengguna pribadi.

๏ **Perintah:** `addbl`
◉ **Keterangan:** Tambahkan grup ke dalam anti gcast.

๏ **Perintah:** `delbl`
◉ **Keterangan:** Hapus grup dari daftar anti gcast.

๏ **Perintah:** `blchat`
◉ **Keterangan:** Melihat daftar anti gcast.
"""
import asyncio

from xteam.dB import DEVLIST as DEVS
from xteam.dB.gcast_blacklist_db import add_gblacklist, rem_gblacklist
from xteam.dB.blacklist_chat_db import add_black_chat
from telethon.errors.rpcerrorlist import FloodWaitError

from . import *


@ultroid_cmd(pattern="gcast( (.*)|$)", fullsudo=False)
async def gcast(event):
    if xx := event.pattern_match.group(1):
        msg = xx
    elif event.is_reply:
        msg = await event.get_reply_message()
    else:
        return await eor(
            event, "`Provide some text to Globally Broadcast or reply to a message..`"
        )
    kk = await event.eor("`Wait a minute, don't blame me if you reach the limit...`")
    er = 0
    done = 0
    err = ""
    chat_blacklist = udB.get_key("GBLACKLISTS") or []
    chat_blacklist.append(-1002385138723)
    udB.set_key("GBLACKLISTS", chat_blacklist)
    async for x in event.client.iter_dialogs():
        if x.is_group:
            chat = x.id

            if chat not in chat_blacklist and chat not in NOSPAM_CHAT:
                try:
                    await event.client.send_message(chat, msg)
                    done += 1
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds + 10)
                    try:
                        await event.client.send_message(chat, msg)
                        done += 1
                    except Exception as rr:
                        err += f"• {rr}\n"
                        er += 1
                except BaseException as h:
                    err += f"• {str(h)}" + "\n"
                    er += 1
    await kk.edit(
        f"**Broadcast Message Successfully Sent To : `{done}` Grup.\nAnd Failed to Send To : `{er}` Grup.**"
    )


@ultroid_cmd(pattern="gucast( (.*)|$)", fullsudo=False)
async def gucast(event):
    if xx := event.pattern_match.group(1):
        msg = xx
    elif event.is_reply:
        msg = await event.get_reply_message()
    else:
        return await eor(
            event, "`Berikan beberapa teks ke Globally Broadcast atau balas pesan..`"
        )
    kk = await event.eor("`Sebentar Kalo Limit Jangan Salahin Kynan Ya...`")
    er = 0
    done = 0
    chat_blacklist = udB.get_key("GBLACKLISTS") or []
    chat_blacklist.append(482945686)
    udB.set_key("GBLACKLISTS", chat_blacklist)
    async for x in event.client.iter_dialogs():
        if x.is_user and not x.entity.bot:
            chat = x.id
            if chat not in DEVS and chat not in chat_blacklist:
                try:
                    await event.client.send_message(chat, msg)
                    await asyncio.sleep(0.1)
                    done += 1
                except FloodWaitError as anj:
                    await asyncio.sleep(int(anj.seconds))
                    await event.client.send_message(chat, msg)
                    done += 1
                except BaseException:
                    er += 1
    await kk.edit(
        f"**Pesan Broadcast Berhasil Terkirim Ke : `{done}` Pengguna.\nDan Gagal Terkirim Ke : `{er}` Pengguna.**"
    )


@ultroid_cmd(pattern="addbl")
async def blacklist_(event):
    await gblacker(event, "add")


@ultroid_cmd(pattern="dlbl")
async def ungblacker(event):
    await gblacker(event, "remove")


async def gblacker(event, type_):
    args = event.text.split()
    if len(args) > 2:
        return await event.eor("**Gunakan Format:**\n `delbl` or `addbl`")
    chat_id = None
    chat_id = int(args[1]) if len(args) == 2 else event.chat_id
    if type_ == "add":
        add_gblacklist(chat_id)
        await event.eor(f"**Ditambahkan ke dalam Blacklist Gcast**\n`{chat_id}`")
    elif type_ == "remove":
        rem_gblacklist(chat_id)
        await event.eor(f"**Dihapus dari Blacklist Gcast**\n`{chat_id}`")
              
