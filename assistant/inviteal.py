import asyncio
from telethon import TelegramClient, events, functions
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import InputPeerChannel, InputPeerChat
from pyUltroid._misc._assistant import asst, ultroid_bot as client

async def get_chatinfo(event):
    chat = await event.get_chat()
    if isinstance(chat, (InputPeerChannel, InputPeerChat)):
        try:
            full_chat = await client(GetFullChatRequest(chat.id))
            return full_chat
        except Exception as e:
            await event.reply(f"Error getting chat info: {e}")
            return None
    else:
        return None

@client.on(events.NewMessage(pattern=r'/inviteall'))
async def invite_all(event):
    sender = await event.get_sender()
    me = await client.get_me()
    if not sender.id == me.id:
        rkp = await event.reply("`processing...`")
    else:
        rkp = await event.edit("`processing...`")
    rk1 = await get_chatinfo(event)
    chat = await event.get_chat()
    if event.is_private:
        return await rkp.edit("`Sorry, Can add users here`")
    s = 0
    f = 0
    error = "None"

    await rkp.edit("**TerminalStatus**\n\n`Collecting Users.......`")
    if rk1 and rk1.full_chat:
        async for user in client.iter_participants(rk1.full_chat.id):
            try:
                if error.startswith("Too"):
                    return await rkp.edit(
                        f"**Terminal Finished With Error**\n(`May Got Limit Error from telethon Please try agin Later`)\n**Error** : \n`{error}`\n\n• Invited `{s}` people \n• Failed to Invite `{f}` people"
                    )
                await client(
                    functions.channels.InviteToChannelRequest(channel=chat, users=[user.id])
                )
                s = s + 1
                await rkp.edit(
                    f"**Terminal Running...**\n\n• Invited `{s}` people \n• Failed to Invite `{f}` people\n\n**× LastError:** `{error}`"
                )
                await asyncio.sleep(1) #Add a small delay to prevent flood waits.
            except Exception as e:
                error = str(e)
                f = f + 1
        return await rkp.edit(
            f"**Terminal Finished** \n\n• Successfully Invited `{s}` people \n• failed to invite `{f}` people"
        )
    else:
        await rkp.edit("Error getting chat information.")
