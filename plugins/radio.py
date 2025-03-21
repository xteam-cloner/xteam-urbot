from telethon import TelegramClient, events, utils
import os
import subprocess
import asyncio
from . import *

radio_url = 'http://stream.zenolive.com/8wv4d8g4344tv'  # Ganti dengan URL siaran radio Anda

# Nama grup atau channel tempat siaran radio akan diputar
chat_username = 'xteam_cloner'  # Ganti dengan username grup atau channel Anda

radio_process = None

async def start_radio(event):
    """Memulai pemutaran siaran radio."""
    global radio_process
    if radio_process and radio_process.poll() is None:
        await event.respond('Siaran radio sudah berjalan.')
        return

    try:
        radio_process = subprocess.Popen(['ffmpeg', '-i', radio_url, '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', '48000', '-ac', '2', 'pipe:1'], stdout=subprocess.PIPE)
        await event.respond('Memulai siaran radio...')
        while radio_process.poll() is None:
            audio_chunk = radio_process.stdout.read(1920)
            if not audio_chunk:
                break
            await ultroid_bot.send_voice(chat_username, audio_chunk)
        await event.respond('Siaran radio berakhir.')
    except Exception as e:
        await event.respond(f'Terjadi kesalahan: {e}')

async def stop_radio(event):
    """Menghentikan pemutaran siaran radio."""
    global radio_process
    if radio_process and radio_process.poll() is None:
        radio_process.terminate()
        await event.respond('Siaran radio dihentikan.')
    else:
        await event.respond('Tidak ada siaran radio yang sedang berjalan.')

@ultroid_cmd(pattern="startradio")
async def handle_start(event):
    """Menangani perintah /startradio."""
    await start_radio(event)

@ultroid_cmd(pattern="stopradio")
async def handle_stop(event):
    """Menangani perintah /stopradio."""
    await stop_radio(event)
