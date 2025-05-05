# 🍀 © @tofik_dn
# FROM Man-Userbot <https://github.com/mrismanaziz/Man-Userbot>
# t.me/SharingUserbot & t.me/Lunatic0de
# ⚠️ Do not remove credits

from secrets import choice
from telethon.tl.types import InputMessagesFilterVideo, InputMessagesFilterVoice
from telethon.tl.types import InputMessagesFilterPhotos
from telethon import events
from telethon.utils import get_display_name
from . import eor, ultroid_cmd, get_string, OWNER_NAME


async def fetch_and_send(event, channel, filter_type, caption=None):
    xx = await event.reply(get_string("asupan_1"))
    try:
        items = [
            item
            async for item in event.client.iter_messages(
                channel, filter=filter_type
            )
        ]
        if items:
            await event.client.send_file(
                event.chat_id,
                file=choice(items),
                caption=caption,
                reply_to=event.reply_to_msg_id,
            )
            await xx.delete()
        else:
            await xx.edit(f"**Tidak bisa menemukan item dari {channel}.**")
    except Exception as e:
        await xx.edit(f"**Terjadi kesalahan saat mengambil item dari {channel}:** `{e}`")


@ultroid_cmd(pattern="asupan$")
async def asupan_cmd(event):
    await fetch_and_send(
        event, "@xcryasupan", InputMessagesFilterVideo, caption=f"Asupan BY 🥀{OWNER_NAME}🥀"
    )


@ultroid_cmd(pattern="pap$")
async def pap_cmd(event):
    await fetch_and_send(event, "@CeweLogoPack", InputMessagesFilterPhotos)


@ultroid_cmd(pattern="ppcp$")
async def ppcp_cmd(event):
    await fetch_and_send(event, "@ppcpcilik", InputMessagesFilterPhotos, caption="Couple PAP")


@ultroid_cmd(pattern="desah$")
async def desah_cmd(event):
    await fetch_and_send(event, "@desahancewesangesange", InputMessagesFilterVoice, caption="Desahan Cewe")


@ultroid_cmd(pattern="asupancb$")
async def asupancb_cmd(event):
    buttons = [
        [events.CallbackQuery(data=b"asupan")],
        [events.CallbackQuery(data=b"pap")],
        [events.CallbackQuery(data=b"ppcp")],
        [events.CallbackQuery(data=b"desah")],
    ]
    await event.reply(
        "Pilih asupan berdasarkan kategori:", buttons=buttons, reply_to=event.reply_to_msg_id
    )


@ultroid_cmd(pattern="asupancbg$")
async def asupancbg_cmd(event):
    buttons = [
        [
            events.CallbackQuery(data=b"asupan"),
            events.CallbackQuery(data=b"pap"),
        ],
        [
            events.CallbackQuery(data=b"ppcp"),
            events.CallbackQuery(data=b"desah"),
        ],
    ]
    await event.reply(
        "Pilih asupan:", buttons=buttons, reply_to=event.reply_to_msg_id
    )


@ultroid_cmd(pattern="asupancbi$")
async def asupancbi_cmd(event):
    inline_keyboard = [
        [("Video Asupan", "asupan")],
        [("Foto PAP", "pap")],
        [("Foto PP Couple", "ppcp")],
        [("Suara Desahan", "desah")],
    ]
    await event.reply(
        "Pilih jenis asupan:", buttons=inline_keyboard, reply_to=event.reply_to_msg_id
    )


@events.register(events.CallbackQuery(pattern=b"asupan"))
async def asupan_callback(event):
    await fetch_and_send(
        event, "@xcryasupan", InputMessagesFilterVideo, caption=f"Asupan BY 🥀{OWNER_NAME}🥀"
    )
    await event.answer("Mengirim video asupan...")


@events.register(events.CallbackQuery(pattern=b"pap"))
async def pap_callback(event):
    await fetch_and_send(event, "@CeweLogoPack", InputMessagesFilterPhotos)
    await event.answer("Mengirim foto PAP...")


@events.register(events.CallbackQuery(pattern=b"ppcp"))
async def ppcp_callback(event):
    await fetch_and_send(event, "@ppcpcilik", InputMessagesFilterPhotos, caption="Couple PAP")
    await event.answer("Mengirim foto PP Couple...")


@events.register(events.CallbackQuery(pattern=b"desah"))
async def desah_callback(event):
    await fetch_and_send(event, "@desahancewesangesange", InputMessagesFilterVoice, caption="Desahan Cewe")
    await event.answer("Mengirim suara desahan...")
