from telethon import TelegramClient, events
from pytgcalls import PyTgCalls
from pytgcalls import filters as fl
from pytgcalls.types import ChatUpdate, GroupCallParticipant, StreamEnded, Update, UpdatedGroupCallParticipant
import os
from pyUltroid.configs import Var
# Replace with your API ID, API hash, and session string

#if not API_ID or not API_HASH or not SESSION_STRING:
    #raise ValueError("API_ID, API_HASH, and SESSION_STRING must be set as environment variables.")

client = TelegramClient(Var.SESSION, Var.API_ID, Var.API_HASH)
call_py = PyTgCalls(client)

async def start_calls():
    await call_py.start()

@client.on(events.NewMessage(pattern='!play'))
async def play_handler(event):
    await call_py.play(
        event.chat_id,
        'http://docs.evostream.com/sample_content/assets/sintel1m720p.mp4',
    )

@client.on(events.NewMessage(pattern='!record'))
async def record_handler(event):
    await call_py.record(
        event.chat_id,
        'record.mp3',
    )

@client.on(events.NewMessage(pattern='!cache'))
async def cache_handler(event):
    print(call_py.cache_peer)

@client.on(events.NewMessage(pattern='!ping'))
async def ping_handler(event):
    print(call_py.ping)

@client.on(events.NewMessage(pattern='!pause'))
async def pause_handler(event):
    await call_py.pause(
        event.chat_id,
    )

@client.on(events.NewMessage(pattern='!resume'))
async def resume_handler(event):
    await call_py.resume(
        event.chat_id,
    )

@client.on(events.NewMessage(pattern='!stop'))
async def stop_handler(event):
    await call_py.leave_call(
        event.chat_id,
    )

@client.on(events.NewMessage(pattern='!change_volume'))
async def change_volume_handler(event):
    await call_py.change_volume_call(
        event.chat_id,
        50,
    )

@client.on(events.NewMessage(pattern='!status'))
async def get_play_status(event):
    await event.respond(f'Current seconds {await call_py.time(event.chat_id)}')

@call_py.on_update(fl.chat_update(ChatUpdate.Status.KICKED | ChatUpdate.Status.LEFT_GROUP))
async def kicked_handler(_: PyTgCalls, update: ChatUpdate):
    print(f'Kicked from {update.chat_id} or left')

@call_py.on_update(fl.stream_end())
async def stream_end_handler(_: PyTgCalls, update: StreamEnded):
    print(f'Stream ended in {update.chat_id}', update)

@call_py.on_update(fl.call_participant(GroupCallParticipant.Action.JOINED))
async def participant_handler(_: PyTgCalls, update: UpdatedGroupCallParticipant):
    print(f'Participant joined in {update.chat_id}', update)

@call_py.on_update()
async def all_updates(_: PyTgCalls, update: Update):
    print(update)

async def main():
    await client.start()
    await start_calls()
    print("Telethon client and PyTgCalls started. Userbot is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
