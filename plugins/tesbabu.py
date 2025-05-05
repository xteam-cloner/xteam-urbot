# 🍀 © @tofik_dn
# FROM Man-Userbot <https://github.com/mrismanaziz/Man-Userbot>
# t.me/SharingUserbot & t.me/Lunatic0de
# ⚠️ Do not remove credits

from secrets import choice
from telethon.tl.types import (
    InputMessagesFilterVideo,
    InputMessagesFilterVoice,
    InputMessagesFilterPhotos,
    InlineQueryResultDocument,
    InlineQueryResultPhoto,
    InlineQueryResultAudio,
    DocumentAttributeFilename,
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaVoice,
)
from telethon.utils import get_display_name
from telethon.errors import QueryIdInvalidError
from . import eor, ultroid_cmd, get_string, OWNER_NAME, bot


@ultroid_cmd(pattern="asupan$")
async def _(event):
    xx = await event.eor(get_string("asupan_1"))
    try:
        asupannya = [
            asupan
            async for asupan in event.client.iter_messages(
                "@xcryasupan", filter=InputMessagesFilterVideo
            )
        ]
        await event.client.send_file(
            event.chat_id,
            file=choice(asupannya),
            caption=f"Asupan BY 🥀{OWNER_NAME}🥀",
            reply_to=event.reply_to_msg_id,
        )
        await xx.delete()
    except Exception:
        await xx.edit("**Tidak bisa menemukan video asupan.**")


@ultroid_cmd(pattern="pap$")
async def _(event):
    xx = await event.eor(get_string("asupan_1"))
    try:
        papnya = [
            pap
            async for pap in event.client.iter_messages(
                "@CeweLogoPack", filter=InputMessagesFilterPhotos
            )
        ]
        await event.client.send_file(
            event.chat_id, file=choice(papnya), reply_to=event.reply_to_msg_id
        )
        await xx.delete()
    except Exception:
        await xx.edit("**Tidak bisa menemukan pap.**")


@ultroid_cmd(pattern="ppcp$")
async def _(event):
    xx = await event.eor(get_string("asupan_1"))
    try:
        ppcpnya = [
            ppcp
            async for ppcp in event.client.iter_messages(
                "@ppcpcilik", filter=InputMessagesFilterPhotos
            )
        ]
        await event.client.send_file(
            event.chat_id, file=choice(ppcpnya), reply_to=event.reply_to_msg_id
        )
        await xx.delete()
    except Exception:
        await xx.edit("**Tidak bisa menemukan pap couple.**")


@ultroid_cmd(pattern="desah$")
async def _(event):
    xx = await event.eor(get_string("asupan_1"))
    try:
        desahcewe = [
            desah
            async for desah in event.client.iter_messages(
                "@desahancewesangesange", filter=InputMessagesFilterVoice
            )
        ]
        await event.client.send_file(
            event.chat_id, file=choice(desahcewe), reply_to=event.reply_to_msg_id
        )
        await xx.delete()
    except Exception:
        await xx.edit("**Tidak bisa menemukan desahan cewe.**")


@bot.on(pattern="^/inline_asupan")
async def inline_asupan_query(event):
    builder = event.builder
    result = None
    query = event.text.split(None, 1)[1] if event.text else None

    if query:
        if query.lower() == "video":
            asupannya = [
                asupan
                async for asupan in event.client.iter_messages(
                    "@xcryasupan", filter=InputMessagesFilterVideo, limit=10
                )
            ]
            results = []
            for asupan in asupannya:
                if asupan.media:
                    results.append(
                        builder.document(
                            asupan.media,
                            title="Video Asupan",
                            text=f"Asupan BY 🥀{OWNER_NAME}🥀",
                        )
                    )
            await event.answer(results)
        elif query.lower() == "pap":
            papnya = [
                pap
                async for pap in event.client.iter_messages(
                    "@CeweLogoPack", filter=InputMessagesFilterPhotos, limit=10
                )
            ]
            results = []
            for pap in papnya:
                if pap.media:
                    results.append(
                        builder.photo(pap.media, text=f"PAP BY 🥀{OWNER_NAME}🥀")
                    )
            await event.answer(results)
        elif query.lower() == "ppcp":
            ppcpnya = [
                ppcp
                async for ppcp in event.client.iter_messages(
                    "@ppcpcilik", filter=InputMessagesFilterPhotos, limit=10
                )
            ]
            results = []
            for ppcp in ppcpnya:
                if ppcp.media:
                    results.append(
                        builder.photo(ppcp.media, text=f"PPCp BY 🥀{OWNER_NAME}🥀")
                    )
            await event.answer(results)
        elif query.lower() == "desah":
            desahcewe = [
                desah
                async for desah in event.client.iter_messages(
                    "@desahancewesangesange", filter=InputMessagesFilterVoice, limit=10
                )
            ]
            results = []
            for desah in desahcewe:
                if desah.media:
                    results.append(
                        builder.audio(
                            desah.media, title="Desahan Cewe", performer=OWNER_NAME
                        )
                    )
            await event.answer(results)
        else:
            await event.answer(
                [
                    builder.article(
                        title="Pilih Kategori",
                        text="Silakan pilih kategori asupan yang Anda inginkan:",
                        buttons=[
                            [("Video", "inline_asupan video")],
                            [("Foto (PAP)", "inline_asupan pap")],
                            [("Foto Couple (PPCp)", "inline_asupan ppcp")],
                            [("Suara (Desah)", "inline_asupan desah")],
                        ],
                    )
                ]
            )
    else:
        await event.answer(
            [
                builder.article(
                    title="Pilih Kategori",
                    text="Silakan pilih kategori asupan yang Anda inginkan:",
                    buttons=[
                        [("Video", "inline_asupan video")],
                        [("Foto (PAP)", "inline_asupan pap")],
                        [("Foto Couple (PPCp)", "inline_asupan ppcp")],
                        [("Suara (Desah)", "inline_asupan desah")],
                    ],
                )
            ]
        )
        
