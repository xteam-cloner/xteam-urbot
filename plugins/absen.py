# Ayiin - Userbot
# Copyright (C) 2022-2023 @AyiinXd
#
# This file is a part of < https://github.com/AyiinXd/Ayiin-Userbot >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/AyiinXd/Ayiin-Userbot/blob/main/LICENSE/>.
#
# FROM Ayiin-Userbot <https://github.com/AyiinXd/Ayiin-Userbot>
# t.me/AyiinXdSupport & t.me/AyiinSupport

# ========================×========================
#            Jangan Hapus Credit Ngentod
# ========================×========================

import time
from datetime import datetime
from secrets import choice 
from pyUltroid.dB import devs
from telethon.tl.types import User
from pyUltroid._misc import sudoers
from . import cmd, get_string, inline_mention, udB, ultroid_bot
from . import ultroid_cmd as ayiinCmd 


absen = [
    "**𝙃𝙖𝙙𝙞𝙧 𝙙𝙤𝙣𝙜 𝙏𝙤𝙙** 😁",
    "**𝙃𝙖𝙙𝙞𝙧 𝙆𝙖𝙠𝙖 𝙂𝙖𝙣𝙩𝙚𝙣𝙜** 😉",
    "**𝙂𝙪𝙖 𝙃𝙖𝙙𝙞𝙧 𝘾𝙤𝙣𝙩𝙤𝙡** 😁",
    "**𝙂𝙪𝙖 𝙃𝙖𝙙𝙞𝙧 𝙂𝙖𝙣𝙩𝙚𝙣𝙜** 🥵",
    "**𝙃𝙖𝙙𝙞𝙧 𝙉𝙜𝙖𝙗** 😎",
    "**𝙂𝙪𝙖 𝙃𝙖𝙙𝙞𝙧 𝘼𝙗𝙖𝙣𝙜** 🥺",
    "**𝙎𝙞 𝘾𝙖𝙠𝙚𝙥 𝙃𝙖𝙙𝙞𝙧 𝘽𝙖𝙣𝙜** 😎",
]

ayiincakep = [
    "**𝙄𝙮𝙖 𝙂𝙖𝙣𝙩𝙚𝙣𝙜 𝘽𝙖𝙣𝙜𝙚𝙩** 😍",
    "**𝙂𝙖𝙣𝙩𝙚𝙣𝙜𝙣𝙮𝙖 𝙂𝙖𝙠 𝘼𝙙𝙖 𝙇𝙖𝙬𝙖𝙣** 😚",
    "**𝙠𝙖𝙢𝙪 𝙂𝙖𝙣𝙩𝙚𝙣𝙜𝙣𝙮𝙖 𝘼𝙠𝙪 𝙆𝙖𝙣** 😍",
    "**𝙞𝙮𝙖𝙖 𝙜𝙖𝙙𝙖 𝙖𝙙𝙖 𝙨𝙖𝙞𝙣𝙜** 😎",
    "**𝙠𝙖𝙢𝙪 𝙟𝙖𝙢𝙚𝙩 𝙏𝙖𝙥𝙞 𝘽𝙤𝙤𝙣𝙜** 😚",
]


@ayiinCmd("cping$", devs=True)
async def _(ping):
    start = time.time()
    x = await event.eor("Pong !")
    end = round((time.time() - start) * 1000)
    uptime = time_formatter((time.time() - start_time) * 1000)
    user = await ping.client.get_me()
    message = "**✧ ᴀʏɪɪɴ-ᴜsᴇʀʙᴏᴛ ✧**\n\n✧ **ᴘɪɴɢᴇʀ :** `{} ms`\n✧ **ᴜᴘᴛɪᴍᴇ :** `{}`\n✧ **ᴏᴡɴᴇʀ :** `{}`\n✧ **ɪᴅ :** `{}`"
    await ping.reply(
        message.format(
            duration,
            uptime,
            user.first_name,
            user.id
        )
    )


# KALO NGEFORK absen ini GA USAH DI HAPUS YA GOBLOK 😡
# JANGAN DI HAPUS GOBLOK 😡 LU COPY AJA TINGGAL TAMBAHIN
# DI HAPUS GUA GBAN YA 🥴 GUA TANDAIN LU AKUN TELENYA 😡

# Absen by : mrismanaziz <https://github.com/mrismanaziz/man-userbot>

@ayiinCmd("absen$", devs=True)
async def ayiinabsen(ganteng):
    await ganteng.reply(choice(absen))


@ayiinCmd("Aku ganteng kan$", devs=True)
async def ayiin(ganteng):
    await ganteng.reply(choice(ayiincakep))


# ========================×========================
#            Jangan Hapus Credit Ngentod
# ========================×========================

