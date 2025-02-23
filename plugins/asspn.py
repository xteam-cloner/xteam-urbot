from telethon import events, types, functions
from telethon.tl.types import InputMessagesFilterVideo
from random import choice
from . import *
from . import eor, ultroid_cmd, get_string, OWNER_NAME
import logging

logging.basicConfig(level=logging.ERROR)

@events.InlineQuery
async def inline_asupan(event):
    builder = event.builder
    query = event.text.lower()
    if "asupan" in query:
        try:
            asupannya = [
                asupan
                async for asupan in event.client.iter_messages(
                    "@xcryasupan", filter=InputMessagesFilterVideo, limit=2
                )
            ]
            if asupannya:
                asupan_choice = choice(asupannya)
                result = builder.article(
                    title="Asupan Video",
                    text=f"Asupan BY 🥀{OWNER_NAME}🥀",
                    file=asupan_choice,
                )
                await event.answer([result])
            else:
                await event.answer([builder.article("Tidak ditemukan", text="Tidak ada video asupan ditemukan.")])

        except Exception as e:
            logging.error(f"Error in inline_asupan: {e}")
            await event.answer([builder.article("Error", text="Terjadi kesalahan saat mencari asupan.")])
            
