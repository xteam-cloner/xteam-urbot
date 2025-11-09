from . import *
from telethon import events
from youtube_dl import YoutubeDL

ydl = YoutubeDL({'outtmpl': '%(id)s%(ext)s'})

@ultroid_cmd(pattern="play")
async def panggil(event):
    query = event.text.split(" ", 1)[1]
    try:
        info = ydl.extract_info(query, download=False)
        url = info['formats'][0]['url']
        await ntgcalls.call(event.chat_id, url)
    except Exception as e:
        await event.respond(f"Error: {e}")

@ultroid_cmd(pattern="end")
async def akhiri(event):
    chat_id = event.chat_id
    await ntgcalls.leave(chat_id)


@ultroid_cmd(pattern="joinvc")
async def vc(event):
    try:
        chat_id = event.chat_id
        await ntgcalls.join_vc(chat_id)
    except Exception as e:
        await event.respond(f"Error: {e}")

@ultroid_cmd(pattern="leavevc")
async def akhiri_vc(event):
    try:
        chat_id = event.chat_id
        await ntgcalls.leave_vc(chat_id)
    except Exception as e:
        await event.respond(f"Error: {e}")
