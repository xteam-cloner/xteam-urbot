from telethon import events, types, functions
from telethon.tl.types import InputMessagesFilterVideo, InputMessagesFilterPhotos
from random import choice
from . import *
@events.InlineQuery
async def inline_asupan(event):
    builder = event.builder
    query = event.text.lower()
    if "asupan" in query:
        try:
            asupannya = [
                asupan
                async for asupan in event.client.iter_messages(
                    "@xcryasupan", filter=InputMessagesFilterVideo
                )
            ]
            if asupannya:
                asupan_choice = choice(asupannya)
                result = builder.article(
                    title="Asupan Video",
                    text="Asupan BY 🥀{OWNER_NAME}🥀", #Replace OWNER_NAME with real value
                    file=asupan_choice,
                )
                await event.answer([result])
            else:
                await event.answer([builder.article("Tidak ditemukan", text="Tidak ada video asupan ditemukan.")])

        except Exception as e:
            print(e)
            await event.answer([builder.article("Error", text="Terjadi kesalahan saat mencari asupan.")])
          
