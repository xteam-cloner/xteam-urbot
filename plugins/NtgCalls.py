import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.phone import CreateGroupCallRequest, DiscardGroupCallRequest
from ntgcalls import NTgCalls, MediaDescription, AudioDescription, VideoDescription, MediaSource, StreamMode
from . import *

api_id = 22049281
api_hash = '0377071c177fea820b5086cb8298ed64'
wrtc = NTgCalls()

@ultroid_cmd(pattern="joinvc")
async def join_vc(event):
    chat_id = event.chat_id
    call_params = await wrtc.create_call(chat_id)
    await wrtc.set_stream_sources(
        chat_id,
        StreamMode.CAPTURE,
        MediaDescription(
            microphone=AudioDescription(
                media_source=MediaSource.FILE,
                input="output.pcm",
                sample_rate=48000,
                channel_count=2,
            ),
            camera=VideoDescription(
                media_source=MediaSource.FILE,
                input="output.i420",
                width=1280,
                height=720,
                fps=30,
            ),
        ),
    )
    result = await ultroid_bot(functions.phone.CreateGroupCallRequest(
        peer=await ultroid_bot.get_input_entity(chat_id),
        schedule_date=None,
    ))
    await wrtc.connect(chat_id, result.call.id, False)
    await event.edit("Connected!")

@ultroid_cmd(pattern="leavevc")
async def leave_vc(event):
    chat_id = event.chat_id
    await wrtc.disconnect(chat_id)
    await ultroid_bot(functions.phone.DiscardGroupCallRequest(
        call=await wrtc.get_call(chat_id),
    ))
    await event.edit("Disconnected!")
