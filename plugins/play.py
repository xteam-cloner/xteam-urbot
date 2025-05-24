import asyncio
from pyrogram import filters
from xteam.startup.BaseClient import Client, PyTgCalls as Call
from pytgcalls.types import AudioPiped, AudioVideoPiped

# Handler untuk perintah /play
@Client.on_message(filters.command("play") & filters.group)
async def play_music(client: Client, message):
    chat_id = message.chat.id
    query = " ".join(message.command[1:])

    if not query:
        await message.reply_text("Mohon berikan URL atau nama file audio untuk diputar.")
        return
    try:
       await Call.join_group_call(
            chat_id,
            AudioPiped(query), # Sumber audio dari URL atau path file
            stream_type=StreamType().full_audio
        )
        await message.reply_text(f"Memutar: {query}")
    except Exception as e:
        await message.reply_text(f"Gagal memutar musik: {e}")

# Handler untuk perintah /stop
@Client.on_message(filters.command("stop") & filters.group)
async def stop_music(client: Client, message):
    chat_id = message.chat.id
    try:
        await Call.leave_group_call(chat_id)
        await message.reply_text("Musik dihentikan.")
    except Exception as e:
        await message.reply_text(f"Gagal menghentikan musik: {e}")

# Handler untuk perintah /pause
@Client.on_message(filters.command("pause") & filters.group)
async def pause_music(client: Client, message):
    chat_id = message.chat.id
    try:
        await Call.pause_stream(chat_id)
        await message.reply_text("Musik dijeda.")
    except Exception as e:
        await message.reply_text(f"Gagal menjeda musik: {e}")

# Handler untuk perintah /resume
@Client.on_message(filters.command("resume") & filters.group)
async def resume_music(client: Client, message):
    chat_id = message.chat.id
    try:
        await Call.resume_stream(chat_id)
        await message.reply_text("Musik dilanjutkan.")
    except Exception as e:
        await message.reply_text(f"Gagal melanjutkan musik: {e}")
