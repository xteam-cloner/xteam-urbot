from telethon import TelegramClient, events, functions, types
from telethon.errors import ChatAdminRequiredError
from telethon.tl.functions.phone import CreateGroupCallRequest, DiscardGroupCallRequest, EditGroupCallTitleRequest
from telethon.tl.types import InputGroupCall, InputPeerChannel, InputPeerChat
from telethon.utils import get_input_peer
from telethon.errors.rpcerrorlist import PeerIdInvalidError, ChatAdminRequiredError
import asyncio
import os
import random
import config 
from . import ultroid_bot as client 
from pytgcalls import PyTgCalls
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
)
from pytgcalls.types import (
    JoinedGroupCallParticipant,
    LeftGroupCallParticipant,
    MediaStream,
    Update,
)
from pytgcalls.types.stream import StreamAudioEnded

# Initialize the client
client = TelegramClient(session, api_id, api_hash)
call_py = PyTgCalls(client)

active_calls = {}
audio_data = {}
list_data = []

def remove_list(user_id):
    list_data[:] = [item for item in list_data if item.get("id") != user_id]

def add_list(user_id, text):
    data = {"id": user_id, "nama": text}
    list_data.append(data)

def get_list():
    if not list_data:
        return "<b>None</b>"

    msg = "\n".join(item["nama"] for item in list_data)
    return msg

async def get_group_call(event, err_msg: str = "") -> Optional[InputGroupCall]:
    chat_peer = await get_input_peer(event.chat)
    if isinstance(chat_peer, (InputPeerChannel, InputPeerChat)):
        if isinstance(chat_peer, InputPeerChannel):
            full_chat = (await client(functions.channels.GetFullChannelRequest(channel=chat_peer))).full_chat
        elif isinstance(chat_peer, InputPeerChat):
            full_chat = (await client(functions.messages.GetFullChatRequest(chat_id=chat_peer.chat_id))).full_chat
        if full_chat is not None:
            return full_chat.call
    await event.respond(f"<emoji id=5929358014627713883>❌</emoji> **No group call found** {err_msg}")
    return False

async def play_audio(client, chat_id, file_path, reply_to_message):
    try:
        await client(functions.phone.JoinGroupCallRequest(
            peer=await get_input_peer(chat_id),
            invite_hash=None,
            muted=False,
            video_muted=True,
            file_path=file_path,
        ))

        if reply_to_message.audio:
            duration = reply_to_message.audio.duration
        elif reply_to_message.voice:
            duration = reply_to_message.voice.duration
        else:
            return

        await asyncio.sleep(duration)
        await client(functions.phone.DiscardGroupCallRequest(call=await get_group_call(reply_to_message)))
    except Exception as e:
        print(f"Error during audio playback: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^.joinvc(?: |$)(.*)?'))
async def join_vc(event):
    global active_calls
    client_id = client.me.id
    chat_id = event.chat_id
    args = event.pattern_match.group(1)
    micon = False
    if args and args.startswith("!"):
        micon = True
        chat_id = int(args[1:]) if args[1:].isdigit() else args[1:]
    elif args and args.isdigit():
        chat_id = int(args)

    text = f"• <b>{client.me.first_name} {client.me.last_name or ''}</b> | <code>{chat_id}</code>"

    current_call = active_calls.get(client_id)
    if current_call and current_call != chat_id:
        try:
            await client(functions.phone.DiscardGroupCallRequest(call=await get_group_call(event)))
        except:
            pass
        active_calls.pop(client_id, None)

    if chat_id == active_calls.get(client_id):
        mk = await event.respond("Already joined the Video Chat. Trying to rejoin...")
        try:
            await client(functions.phone.JoinGroupCallRequest(peer=await get_input_peer(chat_id), muted=not micon, video_muted=True))
            await mk.edit("<b><blockquote>Rejoined the Video Chat.</blockquote></b>")
            return
        except Exception as e:
            await event.respond(f"Failed to rejoin: {str(e)}")
            return

    try:
        await client(functions.phone.JoinGroupCallRequest(peer=await get_input_peer(chat_id), muted=not micon, video_muted=True))
    except ChatAdminRequiredError:
        return await event.respond("Video Chat Not Found & I can't start a voice chat because I'm not an administrator.")
    except PeerIdInvalidError:
        return await event.respond("Invalid chat ID or username.")
    except Exception as e:
        return await event.respond(f"Unexpected error: {str(e)}")

    await event.respond("<b><blockquote>Joined the Video Chat.</blockquote></b>")
    active_calls[client_id] = chat_id
    add_list(client.me.id, text)

@client.on(events.NewMessage(pattern=r'(?i)^.play(?: |$)(.*)?'))
async def play_audio_cmd(event):
    client_id = client.me.id
    chat_id = event.chat_id
    if not event.reply_to_msg or not (event.reply_to_msg.audio or event.reply_to_msg.voice):
        return await event.respond("Please reply to an audio or voice message to play")

    file = event.reply_to_msg
    msg = await event.respond("<b><i>Please wait...</i></b>")
    dl = await client.download_media(file)

    audio_data[client_id] = {"file": dl, "chat_id": chat_id, "message": msg, "reply_message": event.reply_to_msg}

    await play_audio(client, audio_data[client_id]["chat_id"], audio_data[client_id]["file"], audio_data[client_id]["reply_message"])
    os.remove(audio_data[client_id]["file"])
    audio_data.pop(client_id, None)
    await msg.edit("<b>Ended!</b>")

@client.on(events.NewMessage(pattern=r'(?i)^.leavevc(?: |$)(.*)?'))
async def leave_vc(event):
    client_id = client.me.id
    chat_id = event.chat_id
    args = event.pattern_match.group(1)
    if args and args.isdigit():
        chat_id = int(args)
    try:
        await client(functions.phone.DiscardGroupCallRequest(call=await get_group_call(event)))
        remove_list(client.me.id)
        await event.respond("<blockquote><b>Left the Video Chat.</b></blockquote>")
    except Exception as e:
        await event.respond(f"ERROR: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^.startvc(?: |$)(.*)?'))
async def start_vc(event):
    vctitle = event.pattern_match.group(1)
    mk = await event.respond("`Processing....`")
    chat_id = event.chat_id
    args = f"<blockquote><b>Video Chat started</b>\n • <b>Chat</b> : {event.chat.title}</blockquote>"

    try:
        if not vctitle:
            await client(CreateGroupCallRequest(peer=await get_input_peer(chat_id), random_id=random.randint(10000, 999999999)))
        else:
            args += f"\n • <b>Title:</b> {vctitle}"
            await client(CreateGroupCallRequest(peer=await get_input_peer(chat_id), random_id=random.randint(10000, 999999999), title=vctitle))
        await mk.edit(args)
    except ChatAdminRequiredError:
        return await mk.edit("I need to be an administrator to start the video chat.")
    except Exception as e:
        return await mk.edit(f"Error: {str(e)}")

@client.on(events.NewMessage(pattern=r'(?i)^.stopvc'))
async def stop_vc(event):
    mk = await event.respond("`Processing....`")
    try:
        if not (group_call := await get_group_call(event, err_msg=", Error...")):
            return await mk.edit("No active video chat found.")
        await client(DiscardGroupCallRequest(call=group_call))
        await mk.edit(f"<blockquote><b>Video Chat ended</b>\n • <b>Chat</b> : {event.chat.title}</blockquote>")
    except ChatAdminRequiredError:
        return await mk.edit("You need to be an admin to end the video chat.")
    except Exception as e:
        return await mk.edit(f"Error: {str(e)}")
